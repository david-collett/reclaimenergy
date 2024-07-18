# Reclaim Energy Heat Pump (v2) Integration

![Example Screenshot](example.png)

This integration supports heat pump hot water systems from Reclaim Energy which
use the wifi-enabled "v2" controller.

It currently exposes the following entities:

- Water Temperature (at bottom sensor)
- Ambient Temperature
- Heat Pump State (Running / Not Running)
- Power
- Boost switch (Current boost state and ability to turn boost on and off)

Additional sensors and controls are also available, but disabled by default.

To integrate the Power sensor into the energy dashboard, use the "Integral
Sensor" helper to create a Left Riemann sum sensor based on the reclaim power
sensor, this will produce accumulating KWh for use in energy dashboard.

# Installation

TODO
