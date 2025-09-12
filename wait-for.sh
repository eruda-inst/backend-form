#!/bin/sh

host="$1"
port="$2"
shift 2

# Remove o "--" se estiver presente
[ "$1" = "--" ] && shift

cmd="$@"

until nc -z "$host" "$port"; do
  echo "Aguardando $host:$port..."
  sleep 1
done

echo "$host:$port está pronto. Iniciando aplicação..."
exec $cmd
