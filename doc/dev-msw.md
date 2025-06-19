# useful commands

## docker ---------------------------------------------------
### stoped and clean all containers
docker stop $(docker ps -a -q) &&  docker rm $(docker ps -a -q) && docker system prune -f

### clean up docker 
```
docker system prune -f
```

### start container with iris
```
$ docker-compose up -d
```
docker-compose up --build -d
```

### build container with no cache
```
docker-compose build --no-cache --progress=plain
```

## git ------------------------------------
### commit and push
```
git add * && git commit -am "upd" && git push
```
## git stored
```
git config --global credential.helper "cache --timeout=86400"
git config --global credential.helper store
```

## .bashrc -------------------
### User specific aliases and functions
```
alias mc="mc -S dark"
alias hi="history"
alias myip='wget -qO myip http://www.ipchicken.com/; grep -o "[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}" myip;  rm myip'
export PATH=$PATH:/opt/libreoffice6.4/program
```

### PgUp/PgDn
### https://qastack.ru/programming/4200800/in-bash-how-do-i-bind-a-function-key-to-a-command
```
if [[ $- == *i* ]]
then
    bind '"\e[5~": history-search-backward'
    bind '"\e[6~": history-search-forward'
fi
```
### f12
```
bind '"\e[24~":"pwd\n"'
```