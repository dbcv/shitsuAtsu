from django.contrib import admin
from .models import Photo, SegmentedPhoto
from .models import AccessLog

admin.site.register(Photo)
admin.site.register(SegmentedPhoto)

@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'path', 'method', 'ip_address')
    list_filter = (
        'method',
        'user',
        ('timestamp', admin.DateFieldListFilter),  # 日付範囲フィルタ
    )
    search_fields = ('path', 'ip_address', 'user_agent', 'referer')
    readonly_fields = ('timestamp', 'user', 'path', 'method', 'ip_address', 'user_agent', 'referer')
    ordering = ('-timestamp',)

    # 編集を防止（閲覧専用）
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return True  # 手動削除は可