CREATE TYPE "task_action_type" AS ENUM (
  'READY',
  'LOCKED_MAPPING',
  'MAPPED',
  'LOCKED_VALIDATING',
  'VALIDATED',
  'INVALID',
  'BAD',
  'SUBDIVIDED',
  'ARCHIVED',
  'COMMENT'
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
  "effective_megapixels" DECIMAL(10,2),
  "created_at" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "projects" (
  "project_id" UUID PRIMARY KEY,
  "name" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "instructions" TEXT,
  "outline" GEOMETRY(POLYGON,4326),
  "ground_height_meters" SMALLINT,
  "camera_bearings" SMALLINT[],
  "gimble_angles_degrees" SMALLINT[],
  "image_overlap_meters" SMALLINT,
  "hashtags" VARCHAR[],
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
  "created_at" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "task_actions" (
  "action_comment_id" UUID PRIMARY KEY,
  "task_id" INT NOT NULL,
  "user_id" VARCHAR(100) NOT NULL,
  "comment" TEXT,
  "action_type" TASK_ACTION_TYPE NOT NULL,
  "created_at" TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "drone_flights" (
  "flight_id" UUID PRIMARY KEY,
  "drone_id" INT NOT NULL,
  "task_id" INT NOT NULL,
  "user_id" VARCHAR(100) NOT NULL,
  "flight_start" TIMESTAMP,
  "flight_end" TIMESTAMP,
  "override_ground_height_meters" SMALLINT,
  "override_camera_bearings" SMALLINT[],
  "override_gimble_angles_degrees" SMALLINT[],
  "override_image_overlap_meters" SMALLINT,
  "waypoint_file" BYTEA,
  "imagery_data_url" TEXT,
  "created_at" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP)
);

CREATE INDEX "idx_task_id_actions_comments" ON "task_actions" ("task_id");
CREATE INDEX "idx_user_id_actions_comments" ON "task_actions" ("user_id");
CREATE INDEX "idx_actions_comments_action_time" ON "task_actions" ("created_at");
CREATE INDEX "idx_task_id_flights" ON "drone_flights" ("task_id");
CREATE INDEX "idx_user_id_flights" ON "drone_flights" ("user_id");

ALTER TABLE "tasks" ADD FOREIGN KEY ("project_id") REFERENCES "projects" ("project_id");
ALTER TABLE "task_actions" ADD FOREIGN KEY ("task_id") REFERENCES "tasks" ("task_id");
ALTER TABLE "task_actions" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("user_id");
ALTER TABLE "drone_flights" ADD FOREIGN KEY ("drone_id") REFERENCES "drones" ("drone_id");
ALTER TABLE "drone_flights" ADD FOREIGN KEY ("task_id") REFERENCES "tasks" ("task_id");
ALTER TABLE "drone_flights" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("user_id");
