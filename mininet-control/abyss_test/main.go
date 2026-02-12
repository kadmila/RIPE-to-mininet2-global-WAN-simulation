package main

import (
	"crypto/ed25519"
	"flag"
	"fmt"
	"log"
	"os"

	"github.com/kadmila/Abyss-Browser/abyss_core/ahost"
	"golang.org/x/crypto/ssh"
)

func main() {
	// Parse CLI arguments
	var n_peer int
	var id string
	flag.IntVar(&n_peer, "n_peer", 0, "number of peers")
	flag.StringVar(&id, "id", "", "host id")
	flag.Parse()

	// Read ../credentials/{id}.pem and parse key
	key_pem, err := os.ReadFile(fmt.Sprintf("../credentials/%s.pem", id))
	if err != nil {
		log.Fatalf("Error reading private key file: %v", err)
	}
	private_key, err := ssh.ParseRawPrivateKey(key_pem)
	if err != nil {
		log.Fatalf("Error parsing private key: %v", err)
	}

	ed25519_priv_key, ok := private_key.(*ed25519.PrivateKey) //wtf?
	if !ok {
		log.Fatalf("Unsupported key type, expected ed25519 private key")
	}

	// Construct Abyss host
	host, err := ahost.NewAbyssHost(*ed25519_priv_key)
	if err != nil {
		log.Fatalf("Error constructing Abyss host: %v", err)
	}

	err = host.Bind()
	if err != nil {
		log.Fatalf("Error binding Abyss host: %v", err)
	}

	go host.Serve()

	fmt.Println(host.ID(), host.LocalAddrCandidates())
}
