CREATE TYPE "State" AS ENUM (
  'UNLOCKED_TO_MAP',
  'LOCKED_FOR_MAPPING',
  'UNLOCKED_TO_VALIDATE',
  'LOCKED_FOR_VALIDATION',
  'UNLOCKED_DONE'
);

CREATE TABLE "drones" (
  "drone_id" SERIAL PRIMARY KEY,
  "model" VARCHAR(100) NOT NULL,
  "manufacturer" VARCHAR(100),
  "weight_grams" DECIMAL(10,2),
  "min_flight_time_minutes" SMALLINT,
  "max_flight_time_minutes" SMALLINT,
  "max_speed_km_hr" DECIMAL(10,2),
  "max_altitude" SMALLINT,
  "max_payload_grams" SMALLINT,
  "camera_model" VARCHAR(100),
  "image_width_px" INT,
  "image_height_px" INT,
  "sensor_size_mm" INT,
  "focal_length_mm" INT,
  "created_at" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "projects" (
  "project_id" UUID PRIMARY KEY,
  "name" VARCHAR(255) NOT NULL,
  "description" VARCHAR(512),
  "instructions" VARCHAR(512),
  "aoi" GEOMETRY(POLYGON,4326),
  "no_fly_zones" GEOMETRY(POLYGON,4326),
  "ground_sample_distance_cm_px" DECIMAL(10,2),
  "camera_bearings" SMALLINT[],
  "gimble_angles_degrees" SMALLINT[],
  "is_terrain_follow" BOOL,
  "dem_url" VARCHAR(512),
  "hashtags" VARCHAR[],
  "output_raw_url" VARCHAR(512),
  "output_orthophoto_url" VARCHAR(512),
  "output_point_cloud_url" VARCHAR(512),
  "deadline" TIMESTAMP,
  "created_at" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "tasks" (
  "task_id" UUID PRIMARY KEY,
  "project_id" INT NOT NULL,
  "task_number" SMALLINT,
  "geometry" GEOMETRY(POLYGON,4326),
  "created_at" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "users" (
  "user_id" VARCHAR(100) PRIMARY KEY,
  "username" VARCHAR(100) NOT NULL,
  "email" VARCHAR(100) UNIQUE NOT NULL,
  "license_url" VARCHAR(512),
  "license_verified" BOOL,
  "created_at" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "task_events" (
  "event_id" UUID PRIMARY KEY,
  "project_id" INT NOT NULL,
  "task_id" INT NOT NULL,
  "user_id" VARCHAR(100) NOT NULL,
  "comment" VARCHAR(512),
  "state" State NOT NULL,
  "created_at" TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "drone_flights" (
  "flight_id" UUID PRIMARY KEY,
  "drone_id" INT NOT NULL,
  "task_id" INT NOT NULL,
  "user_id" VARCHAR(100) NOT NULL,
  "flight_start" TIMESTAMP,
  "flight_end" TIMESTAMP,
  "user_estimated_battery_time_minutes" SMALLINT,
  "override_camera_bearings" SMALLINT[],
  "override_gimble_angles_degrees" SMALLINT[],
  "override_height_from_ground_meters" SMALLINT,
  "override_image_overlap_percent" SMALLINT,
  "waypoint_file" BYTEA,
  "created_at" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "ground_control_points" (
  "gcp_id" UUID PRIMARY KEY,
  "project_id" INT NOT NULL,
  "image_relative_path" VARCHAR(255) NOT NULL,
  "pixel_x" SMALLINT,
  "pixel_y" SMALLINT,
  "reference_point" GEOMETRY(POLYGON,4326),
  "created_at" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP)
);

CREATE INDEX "idx_task_event_composite " ON "task_events" ("task_id", "project_id");
CREATE INDEX "idx_task_event_project_id_user_id " ON "task_events" ("user_id", "project_id");
CREATE INDEX "idx_task_event_project_id" ON "task_events" ("project_id");
CREATE INDEX "idx_task_event_user_id" ON "task_events" ("user_id");
CREATE INDEX "idx_task_event_created_at" ON "task_events" ("created_at");
CREATE INDEX "idx_task_id_flights" ON "drone_flights" ("task_id");
CREATE INDEX "idx_user_id_flights" ON "drone_flights" ("user_id");

ALTER TABLE "tasks" ADD FOREIGN KEY ("project_id") REFERENCES "projects" ("project_id");
ALTER TABLE "task_events" ADD FOREIGN KEY ("project_id") REFERENCES "projects" ("project_id");
ALTER TABLE "task_events" ADD FOREIGN KEY ("task_id") REFERENCES "tasks" ("task_id");
ALTER TABLE "task_events" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("user_id");
ALTER TABLE "drone_flights" ADD FOREIGN KEY ("drone_id") REFERENCES "drones" ("drone_id");
ALTER TABLE "drone_flights" ADD FOREIGN KEY ("task_id") REFERENCES "tasks" ("task_id");
ALTER TABLE "drone_flights" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("user_id");
ALTER TABLE "ground_control_points" ADD FOREIGN KEY ("project_id") REFERENCES "projects" ("project_id");
