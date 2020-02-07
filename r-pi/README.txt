I was gonna do this 1/x day on an AWS lambda, but it turns out to be more complicated than I thought to have a Lambda with an active internet connection (for pinging the NBA api).

Solution: run it on the raspberry pi I already have doing other 1/x daily backup tasks for me.

The code's already set up to use s3, no problems there
I took care to give it permissions to my bucket, and my bucket only
venv is already installed on the RPi, so I can call run.sh from a cron job easily
