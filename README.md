### Usage

Run your uWSGI server with the stats server enabled, Ex.:

uwsgi --module myapp --socket :3030 --stats /tmp/stats.socket

Then connect uwsgitop to the stats socket

uwsgitop /tmp/stats.socket

more info on http://projects.unbit.it/uwsgi/wiki/StatsServer
