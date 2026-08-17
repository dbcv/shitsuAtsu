from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ..forms import ProfileForm, SimplePasswordChangeForm
from ..models import Profile


@login_required
def setting_view(request):
    profile = Profile.objects.get_or_create(user=request.user)
    profile = profile[0]
    print(request.user.profile)
    print(profile)
    if request.method == "POST":
        profile_form = ProfileForm(request.POST, instance=profile)
        password_form = SimplePasswordChangeForm(request.POST, instance=request.user)
        print("AAA")
        print(password_form.is_valid())
        if "update_profile" in request.POST and profile_form.is_valid():
            profile_form.save()
            messages.success(request, "プロフィールを更新しました。")
            return redirect("setting")
        elif "change_password" in request.POST and password_form.is_valid():
            print("BBB")
            password_form.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "パスワードを変更しました。")
            return redirect("setting")
    else:
        profile_form = ProfileForm(instance=profile)
        password_form = SimplePasswordChangeForm(instance=request.user)

    return render(
        request,
        "myq/setting.html",
        {
            "profile_form": profile_form,
            "password_form": password_form,
        },
    )


@login_required
def change_password(request):
    if request.method == "POST":
        form = SimplePasswordChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("password_change_done")  # 任意の遷移先
    else:
        form = SimplePasswordChangeForm(instance=request.user)

    return render(request, "change_password.html", {"form": form})
