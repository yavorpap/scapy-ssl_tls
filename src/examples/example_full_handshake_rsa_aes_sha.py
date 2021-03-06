#! /usr/bin/env python
# -*- coding: UTF-8 -*-
# Author : tintinweb@oststrom.com <github.com/tintinweb>


def sendrcv(sock, p, bufflen=1024):
    sock.settimeout(5)
    print "sending TLS payload"
    sock.sendall(p)
    resp=''
    try:
        while 1:
            t = sock.recv(1)
            if not(len(t)):
                break
            resp += t
    except:
        print "timeout"
        
        
    print "received, %d --  %s"%(len(resp),repr(resp))
    return resp

if __name__=="__main__":

    import scapy
    from scapy.all import *    
    import socket
    #<----- for local testing only
    sys.path.append("../scapy/layers")
    from ssl_tls import *
    import ssl_tls_crypto
    #------>
    target = ('192.168.220.131',443)            # MAKE SURE TO CHANGE THIS
    
    # create tcp socket
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect(target)
    
    # create TLS Handhsake / Client Hello packet
    p = TLSRecord()/TLSHandshake()/TLSClientHello(compression_methods=None, cipher_suites=[TLSCipherSuite.RSA_WITH_AES_128_CBC_SHA])
                
    p.show()

    r = sendrcv(s,str(p))
    SSL(r).show()

    # send premaster secret
    #p = TLSRecord()/TLSHandshake()/TLSClientKeyExchange()/TLSKexParamDH("haha")


    #generate random premaster secret
    pms = 'a'*48
    # encrypt pms with server pubkey from first cert
    #extract server cert (first one counts)
    cert = SSL(r)[TLSCertificateList].certificates[0].data
    pubkey = ssl_tls_crypto.x509_extract_pubkey_from_der(cert)
    print pubkey
    print pubkey.can_encrypt()
    print pubkey.can_sign()
    print pubkey.publickey()
    
    enc= pubkey.encrypt(pms,None)
    print len(''.join(enc[0])),enc
    pms = ''.join(enc)
    
    p = TLSRecord()/TLSHandshake()/TLSClientKeyExchange()/TLSKexParamEncryptedPremasterSecret(data=pms)
    p.show2()
    
    r = sendrcv(s,str(p))
    SSL(r).show()
    
    # change cipherspec
    p = TLSRecord()/TLSChangeCipherSpec()
    p.show2()
    
    r = sendrcv(s,str(p))
    SSL(r).show()
    
    # send encrypted finish with hash of previous msgs
    # TODO: incomplete
    
    p = TLSRecord()/TLSCiphertext().encrypt(TLSPlaintext().compress(str(TLSHandshake()/TLSFinished().build(pms,"server finished","122"))))
    r = sendrcv(s,str(p))
    SSL(r).show()
    
    s.close()
    
    