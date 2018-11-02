# Deployment

Download your `kubectl` config to `~/.kube/config`


```
# Replace source with your downloaded config
cp ~/Downloads/deploying-oipa-kubeconfig.yaml ~/.kube/config
```

Start your deployment
```sh
kubectl create -f ./deployment.yaml
```

Check the logs
```
kubectl logs -lapp=oipa -c oipa
```

Expose your OIPA container
```
kubectl expose deploy oipa-deployment --port=80 --target-port=8000
```

