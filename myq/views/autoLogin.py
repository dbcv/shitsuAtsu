from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from ..models import AutoLoginToken

def auto_login_view(request):
    token_str = request.GET.get('token')

    if not token_str:
        messages.error(request, 'トークンが見つかりません。')
        return redirect('top_page') # トップページなどにリダイレクト

    try:
        # データベースからトークンを検索
        auto_login_token = AutoLoginToken.objects.get(token=token_str)
        user = auto_login_token.user

        # トークンが期限切れでないかチェック
        if auto_login_token.is_expired():
            messages.error(request, 'このログインリンクは有効期限が切れています。')
            auto_login_token.delete()
            return redirect('top_page')
        
        # ユーザーをログインさせる
        login(request, user)
        
        # ★重要：使用済みのトークンを削除して再利用を防ぐ
        # auto_login_token.delete()
        
        messages.success(request, 'ようこそ！ログインしました。')
        return redirect('home') # ログイン後のダッシュボードなどにリダイレクト

    except AutoLoginToken.DoesNotExist:
        messages.error(request, '無効なログインリンクです。')
        return redirect('home')
