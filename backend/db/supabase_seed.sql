INSERT INTO public.plans (slug, name, daily_merge_limit)
VALUES
    ('starter', 'Starter', 20),
    ('individual', 'Individual', 100),
    ('team', 'Team', 200),
    ('business', 'Business', 9999)
ON CONFLICT (slug) DO UPDATE
SET name = EXCLUDED.name,
    daily_merge_limit = EXCLUDED.daily_merge_limit;
