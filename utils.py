from typing import TypeVar
from bpy.types import Context, Object, Collection


T = TypeVar("T")


def nested_object_generator(root: T, key: str):  # BUG: 子项可能产生循环递归
    """递归套嵌生成器"""
    yield root  # 弹出当前项
    for item in getattr(root, key):  # 遍历root.key下的子项
        for next_item in nested_object_generator(item, key):  # 递归迭代
            yield next_item  # 弹出子项


def filter_current_collections(context: Context) -> list[Collection]:
    """获取当前scene下的collection列表"""
    root = context.scene.collection
    return [
        collection  # 禁止排版缩行.
        for collection in nested_object_generator(root, "children")
    ]


def get_objects_collection(
    context: Context, objects: Object
) -> list[(Object, Collection)]:
    """获取object与collection对应列表"""
    return [
        (obj, collection)
        for collection in filter_current_collections(context)
        for obj in objects
        if obj.name in collection.objects
    ]


def collection_link(objects: list[Object], collection: Collection):
    """批量链接collection"""
    [
        collection.objects.link(obj)
        for obj in objects
        if obj.name not in collection.objects
    ]


def collection_unlink(objects: list[Object], collection: Collection):
    """批量取消链接collection"""
    [
        collection.objects.unlink(obj)
        for obj in objects
        if obj.name in collection.objects
    ]


def objects_move_collection(
    context: Context, objects: list[Object], collection: Collection
):
    """批量移动至collection"""
    obj_coll_list = get_objects_collection(context, objects)

    # 链接目标collection
    collection_link(objects, collection)
    # 筛选非目标collection子项的object对应列表
    obj_coll_list = [
        obj_coll for obj_coll in obj_coll_list if obj_coll[1] != collection
    ]
    unlink_tasks = {}  # 建立字典 {collection: objects}
    for obj_coll in obj_coll_list:
        if obj_coll[1] not in unlink_tasks:
            unlink_tasks[obj_coll[1]] = []
        unlink_tasks[obj_coll[1]].append(obj_coll[0])
    # 取消原链接的collection
    [
        collection_unlink(objects, collection)
        for collection, objects in unlink_tasks.items()
    ]
