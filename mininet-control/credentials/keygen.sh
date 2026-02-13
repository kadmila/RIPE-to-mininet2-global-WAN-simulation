for i in {1..1000}; do
    ssh-keygen -N "" -q -t ed25519 -f h${i}.pem
done

rm *.pub