# A not so intelligent uptime checker.

Pingdom can't check up on our firewalled/internal tools, but pingdumb can!


# TODO

* Implement statuspage.io checks; The script ought to enforce that . Issue; Don't want 200 response codes overriding manual configurations. (example, server starts running slow but responds with 200 status code. Script says 'Healthy!' and admin says 'Degraded', Admin should not be overwritten. Counterpoint: Server times out because nginx isn't running. Admin stops script, starts nginx, then restarts script. The script defaults to thinking it's healhty, and as a result statuspage.io doesnt automatically get reset to 'healhty'

