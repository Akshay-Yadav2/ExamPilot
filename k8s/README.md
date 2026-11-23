# kind

```sh
kind create cluster --name exampilot
make image
kind load docker-image exampilot:dev --name exampilot

# HPA needs metrics-server, and kind needs the insecure TLS flag for it
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl -n kube-system patch deployment metrics-server --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'

kubectl create configmap exampilot-schema --from-file=001_schema.sql=db/schema.sql --from-file=002_topics.sql=db/topics.sql
kubectl create secret generic exampilot \
  --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  --from-literal=EXAMPILOT_TOKEN=change-me \
  --from-literal=DATABASE_URL=postgresql://exampilot:exampilot@postgres:5432/exampilot
kubectl apply -f k8s/
```

Load test from inside the cluster (port-forward pins everything to one pod):

```sh
kubectl run load --rm -it --image=curlimages/curl --restart=Never -- sh -c \
  'i=0; while true; do i=$((i+1)); curl -s -H "Authorization: Bearer change-me" "http://api/search?q=dijkstra+$i" >/dev/null; done'
kubectl get hpa api --watch
```

The query changes every request, otherwise the LRU cache makes it too cheap to scale.
