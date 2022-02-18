XSOCK=/tmp/.X11-unix
XAUTH=/tmp/.docker.xauth-n
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | sudo xauth -f $XAUTH nmerge -
sudo chmod 777 $XAUTH
X11PORT=`echo $DISPLAY | sed 's/^[^:]*:\([^\.]\+\).*/\1/'`
TCPPORT=`expr 6000 + $X11PORT`
sudo ufw allow from 172.17.0.0/16 to any port $TCPPORT proto tcp
DISPLAY=`echo $DISPLAY | sed 's/^[^:]*\(.*\)/172.17.0.1\1/'`
SCRIPTPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

docker run -it \
	-e DISPLAY=${DISPLAY} \
	-e XAUTHORITY=$XAUTH \
	-e MODELICAPATH=/usr/local/JModelica/ThirdParty/MSL:/home/developer/lib \
	-e TERM=xterm-256color \
	-v $XAUTH:$XAUTH \
	-v $SCRIPTPATH:/home/developer/systems:rw \
	-v /home/$USER/Downloads/Buildings\ 7.0.0:/home/developer/lib/Buildings\ 7.0.0:ro \
	--name=jmodelica \
	--rm \
	aviseknaug/jmodelica:2.0

