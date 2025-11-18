--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: web_users; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.web_users (id, username, password_hash, full_name, email, role, is_active, created_at, last_login, login_attempts, locked_until) VALUES (1, 'admin', '$2b$12$O.EteH7Jbyyk5Mqj/djwY.ERvB0mawnbLIj1JAJJawLvyQdFgSYfC', 'System Administrator', 'admin@whac.com', 'admin', true, '2025-10-07 10:01:36.532523', '2025-11-03 13:32:22.373041', 1, '2025-11-05 13:57:46.326134');
INSERT INTO public.web_users (id, username, password_hash, full_name, email, role, is_active, created_at, last_login, login_attempts, locked_until) VALUES (3, 'Mamat', '$2b$12$kZULEywgqEoWGRTnfEIjteKwXX0pOZBHcUgzUm8PNddmvrk3zE6UC', 'Rahmat', 'Rahmat@foom.id', 'operator', true, '2025-10-07 11:43:36.226999', NULL, 0, NULL);
INSERT INTO public.web_users (id, username, password_hash, full_name, email, role, is_active, created_at, last_login, login_attempts, locked_until) VALUES (5, 'Ramadhan', '$2b$12$VjOV8M.6reKYp.JNM.ayIucW2jyBGhGmfVxeNhlWxHVoXmI8pUUEy', 'Ramadhan', 'ramadhan@foom.id', 'operator', true, '2025-10-07 15:55:43.628924', '2025-10-08 12:32:05.187581', 0, NULL);
INSERT INTO public.web_users (id, username, password_hash, full_name, email, role, is_active, created_at, last_login, login_attempts, locked_until) VALUES (2, 'User', '$2b$12$JBcrO5G6OOCz/7mHQPM6kuK4/OEYx3DmWQ4bfgIrRv6oRU90TD.we', 'Hilal', 'hilal@foom.id', 'operator', true, '2025-10-07 10:35:37.496115', '2025-10-08 14:27:02.670498', 0, NULL);
INSERT INTO public.web_users (id, username, password_hash, full_name, email, role, is_active, created_at, last_login, login_attempts, locked_until) VALUES (4, 'Greyoungter', '$2b$12$SKzci1925o8jpEwvCarZ2euN36oMaBQSLBZ7A07HhKiZRRvPC.KYq', 'Hilal Akbar Quddus Ramadhan', 'hakbarqr7333@gmail.com', 'admin', true, '2025-10-07 11:46:42.178375', '2025-10-22 12:27:24.662898', 0, NULL);


--
-- Name: web_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.web_users_id_seq', 5, true);


--
-- PostgreSQL database dump complete
--

