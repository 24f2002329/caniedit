INSERT INTO public.plans (slug, name, daily_merge_limit)
VALUES
    ('starter', 'Starter', 20),
    ('team', 'Team', 200),
    ('business', 'Business', 2000)
ON CONFLICT (slug) DO UPDATE
SET name = EXCLUDED.name,
    daily_merge_limit = EXCLUDED.daily_merge_limit;
