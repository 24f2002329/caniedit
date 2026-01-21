INSERT INTO public.plans (slug, name, daily_merge_limit)
VALUES
    ('starter', 'Starter', 20),
    ('individual', 'Individual', 100),
    ('team', 'Team', 200),
    ('business', 'Business', 9999)
ON CONFLICT (slug) DO UPDATE
SET name = EXCLUDED.name,
    daily_merge_limit = EXCLUDED.daily_merge_limit;

INSERT INTO public.tools (slug, category, weight, is_premium)
VALUES
    ('pdf_merge', 'pdf', 1, false)
ON CONFLICT (slug) DO UPDATE
SET category = EXCLUDED.category,
    weight = EXCLUDED.weight,
    is_premium = EXCLUDED.is_premium;
