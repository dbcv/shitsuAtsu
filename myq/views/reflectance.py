from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from ..models import Photo, SegmentedPhoto
from django.http import FileResponse, JsonResponse, StreamingHttpResponse
import json

class ThreeView(LoginRequiredMixin, generic.DetailView):
    model = SegmentedPhoto
    template_name = 'myq/reflectance.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_queryset(self):
        return SegmentedPhoto.objects.filter(owner=self.request.user)
    
@require_POST
@login_required
def register_reflectance(request):
    try:
        data = json.loads(request.body)
        photo_uuid = data["photo_uuid"]

        photo = get_object_or_404(SegmentedPhoto, uuid=photo_uuid, owner=request.user)
        photo.roughness = data.get('roughness')
        photo.metalness = data.get('metalness')
        photo.albedo = data.get('albedo')
        photo.save(update_fields=["roughness", "metalness", "albedo"])

        return JsonResponse({'status': 'success', 'message': 'Reflectance data registered successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)