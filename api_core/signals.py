from django.dispatch import Signal

bsm_before_create = Signal(providing_args=['apiViewSet', 'new_inst'])
bsm_after_create = Signal(providing_args=['apiViewSet', 'new_inst'])

bsm_before_update = Signal(providing_args=['apiViewSet', 'old_inst', 'new_inst'])
bsm_after_update = Signal(providing_args=['apiViewSet', 'old_inst', 'new_inst'])

bsm_before_delete = Signal(providing_args=['apiViewSet', 'old_inst'])
bsm_after_delete = Signal(providing_args=['apiViewSet', 'old_inst'])
