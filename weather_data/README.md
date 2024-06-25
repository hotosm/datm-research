# Weather Data

- Could be very important for the drone operator on the day.
- Of course we can rely on the operator to know what they are doing and:
  - Not fly on extremely windy days.
  - Judge the wind direction and input that into the flight plan generation.
- However, for the basic user we should probably have a few basic checks.
- Processing weather data from various providers is a bit time consuming and out of scope.
- Luckily, [OpenMeteo](https://open-meteo.com/en/docs) provides a free API for 
  non-commercial use (up to 10000 requests a day), funded by the AWS OpenData Initiative.

## Open Meteo

Using the Weather Forecast API (provide a coordinate), we can:
- Get variables such as wind speed, wind direction, temperature.
- Take the temperature into account to slightly reduce flying time in extreme conditions.
- Adjust the orientation of the flight plan based on prevailing wind direction.

## Other Options

- Windy.com has an API available, but it's paid for.
- We could process the data ourselves on a cron into cloud native data formats we can 
  query.