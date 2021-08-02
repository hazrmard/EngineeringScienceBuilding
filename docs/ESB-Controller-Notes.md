---
title: 'ESB Controller Notes'
order: 1000
hasequations: false
---

## Periods

Timestamps for various system changes.

    2021-03-09 0845-6   System starts reading setpoint, but setpoint is stale
    2021-03-09 0730-6   Controller script restarted, setpoint static
    2021-03-11 1100-6   Controller script restarted, setpoint starts varying
    2021-03-15 1415-5   New version, setpoint capped on top to TempCondOut
    2021-03-18 1220-5   Chiller 1 online
    2021-03-26 1010-5   Chiller 2 online
    2021-05-16 0610-5   Chiller 1 online
    2021-05-23 0610-5   Both chillers offline. Controller script stopped to patch server
    2021-05-24 1240-5   Chiller 1 online. Controller script restarted after patch
    2021-06-08 1329-5   Script stopped to apply patch for Kissam controller
    2021-06-09 1223-5   Script restarted, however output paths were different and not being read
    2021-06-15 1403-5   Script errored, couldn't read BDX due to faulty TLS certificates
    2021-06-16 1240-5   Script restarted with correct paths
    2021-06-17 0505-5   Chiller 2 online (check exact time)

## Timespans to investigate

    2021-03-12 0840-6   2021-03-12 1740-6   Fans on 100%, chiller power smooth
    2021-03-15 1500-5   2021-03-15 1800-5   Fans on 100%, chiller power smooth
    2021-05-23 0610-5   2021-05-24 1240-5   Script stopped, stale setpoint.
    2021-06-08 1329-5   2021-06-09 1223-5   Script stopped, stale setpoint.
    2021-06-15 1403-5   2021-06-16 1240-5   Script errored, stale setpoint