from django.contrib.auth.mixins import LoginRequiredMixin
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import TemplateView

from ..forms import SimpleSignUpForm
from ..models import SegmentedPhoto


class SignUpView(generic.CreateView):
    form_class = SimpleSignUpForm
    success_url = reverse_lazy("login")
    template_name = "myq/signup.html"


class HomeView(TemplateView):
    template_name = "myq/home.html"


class Home3View(LoginRequiredMixin, TemplateView):
    template_name = "myq/home3.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["segmented_photos"] = SegmentedPhoto.objects.filter(
            owner=self.request.user
        ).order_by("-created_at")
        image_count = len(context["segmented_photos"])
        image_url = static(f"image/tree/{('000' + str(int(image_count / 4)))[-3:]}.png")

        context["count_segment"] = [{"imgurl": image_url, "count": image_count}]
        return context


class Start3View(LoginRequiredMixin, TemplateView):
    template_name = "myq/start3.html"
