# Schema Changelog

## v2

- Replaced task_history with task_events + enum refactor.
- Updated indexes on task_events.
- Add no-fly zones to project.
- Rename projects.outline --> projects.aoi.
- Rename projects.ground_height_meters --> height_from_ground_meters.
- Add projects.desired_ground_sample_distance_cm_px
- Rename image_overlap_meters --> image_overlap_percent
- Add projects.is_terrain_follow and projects.dem_url
- Remove projects.height_from_ground_meters and projects.image_overlap_percent, 
  as these is calculated based on desired ground sample distance.
- Update flight param overrides in drone_flights table: 
  override_height_from_ground_meters, override_camera_bearings,
  override_gimble_angles_degrees, override_image_overlap_percent.
  These can only be modified to the extent where they don't affect GSD of
  project.
- Remove drones.effective_megapixels and add additional params to drones table: 
  image_width_px, image_height_px, sensor_size_mm, focal_length_mm
- Add projects.output_orthophoto_url & projects.output_point_cloud_url
- Add projects.deadline timestamp
- Add users.license_url and users.license_verified
- Add drone_flights.user_estimated_battery_time_minutes to allow users to specify
  a flight time that their drone is capable of (they may have a degraded battery
  etc).

## v1

- Initial schema
