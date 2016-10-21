CREATE TABLE tweets (
    user_id bigint NOT NULL,
    raw_text text NOT NULL,
    screen_name character varying(255) NOT NULL,
    lang character varying(50) NOT NULL,
    n_tweets integer NOT NULL
);
