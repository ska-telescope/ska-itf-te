--Postgres Table DDL scripts for 4 new entities to be introduced as a part of PI16
--Currently these tables have an ID as the primary key, info column of jsonb datatype and few additional columns split from the metadata
--The new entities are SBI, Execution Blocks , Projects and Observing Programs

--Create table script for new entities

-- Placeholder for SBDs
CREATE TABLE tab_oda_sbd
(id serial NOT NULL PRIMARY KEY,
info jsonb NOT NULL,
sbd_id text NOT NULL,
version integer NOT NULL,
created_by text NOT NULL,
created_on timestamp NOT NULL,
last_modified_on timestamp NOT NULL,
last_modified_by text NOT NULL);

--Table for SBIS
CREATE TABLE tab_oda_sbi
 (id serial NOT NULL PRIMARY KEY,
 sbd_id text NOT NULL,
 sbd_version serial NOT NULL,
 info jsonb NOT NULL,
 sbi_id text NOT NULL,
 version integer default 1,
 created_by text NOT NULL,
 created_on timestamp NOT NULL,
 last_modified_on timestamp NOT NULL,
 last_modified_by text NOT NULL
);

-- Table for Execution Blocks
CREATE TABLE tab_oda_eb
 (id serial NOT NULL PRIMARY KEY,
 sbd_id text ,
 sbd_version integer ,
 eb_id text NOT NULL,
 info jsonb NOT NULL,
 version integer default 1,
 created_by text NOT NULL,
 created_on timestamp NOT NULL,
 last_modified_on timestamp NOT NULL,
 last_modified_by text NOT NULL );

--Table for Projects
CREATE TABLE tab_oda_prj
 (id serial NOT NULL PRIMARY KEY,
 prj_id text NOT NULL,
 info jsonb NOT NULL,
 version integer default 1,
 author text NOT NULL,
 created_by text NOT NULL,
 created_on timestamp NOT NULL,
 last_modified_on timestamp NOT NULL,
 last_modified_by text NOT NULL );

--Table for Observing Programs
CREATE TABLE tab_oda_obs_prg
 (id serial NOT NULL PRIMARY KEY,
 obs_prg_id text NOT NULL,
 info jsonb NOT NULL,
 version integer default 1,
 created_by text NOT NULL,
 created_on timestamp NOT NULL,
 last_modified_on timestamp NOT NULL,
 last_modified_by text NOT NULL );

