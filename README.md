# pi-autocorrect
A low effort system failure management script for your Raspberry Pi.<br />
<br />
Configure <code>conf.json</code> with the ip's for the pings, <br />
<code>pip3 install -r requirements.txt</code>,<br />
and add the script to your root user's crontab with some check arguments.<br />
Recommended cron line: <code>*/5 * * * * path/to/pi-autocorrect.py --config path/to/conf.json --ping --lanping</code>
