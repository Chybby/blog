CREATE TABLE blogposts (
    id SERIAL PRIMARY KEY,
    title TEXT,
    contents TEXT,
    created_at TIMESTAMP
);

INSERT INTO blogposts VALUES (
    1, 'First Post', 'This is the first post', '2020-01-01 00:00:00'
);