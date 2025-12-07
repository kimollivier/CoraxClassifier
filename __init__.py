# version: 3.0.0
def classFactory(iface):
    from .CoraxImageVideoInspector import CoraxImageVideoInspector
    return CoraxImageVideoInspector(iface)
