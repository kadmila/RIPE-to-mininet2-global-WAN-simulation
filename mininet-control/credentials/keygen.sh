for i in {1..100}; do
    ssh-keygen -N "" -q -t ed25519 -f ${i}.pem
done

rm *.pub