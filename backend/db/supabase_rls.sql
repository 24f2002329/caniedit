ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.files ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (id = auth.uid());

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (id = auth.uid());

CREATE POLICY "Users can view own subscriptions" ON public.subscriptions
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can view own usage" ON public.usage
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert own usage" ON public.usage
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own usage" ON public.usage
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can view own files" ON public.files
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert own files" ON public.files
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can delete own files" ON public.files
    FOR DELETE USING (user_id = auth.uid());
