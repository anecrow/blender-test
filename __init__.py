#######################
# ### bpy imports ### #
import bpy
from bpy.utils import register_class, unregister_class

# ### base class ### #
from bpy.types import Operator, Panel, Context

# ### prop types ### #
from bpy.props import StringProperty, EnumProperty, CollectionProperty

# ### prop group ### #
from bpy.types import PropertyGroup, Scene


#######################
# ### Add_on info ### #
bl_info = {
    "category": "Test",
    "name": "Test",
    "author": "aneCrow",
    "version": (0, 0, 1),
    "blender": (2, 92, 0),
    "description": "",
    "warning": "demo test",
}


# 主面板
class TEST_PT_main(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TEST"
    bl_label = "Test"

    def draw(self, context: Context):  # 绘制函数
        # UI绘制类中禁止直接创建和修改对象的行为
        # 尽量以展示为主,将破坏性动作转至operator类执行
        seleted_objs = context.selected_objects

        layout = self.layout

        if len(seleted_objs) == 0:
            layout.label(text="选择一个对象")


# 次级面板
class sub_Panel(Panel):  # 次级面板基类
    bl_space_type = TEST_PT_main.bl_space_type
    bl_region_type = TEST_PT_main.bl_region_type
    bl_parent_id = TEST_PT_main.__name__

    # 静态函数/类函数,第一个参数指向类本身
    @classmethod  # 静态函数装饰器
    def poll(cls, context):  # 检查函数
        seleted_objs = context.selected_objects
        check = len(seleted_objs) > 0
        return check  # 返回值为空(含False)时,阻止本类实执行和实例化

    # 实例函数,实例化前不可用,第一个参数指向类实例
    def get_selected_objects_collection(self, context: Context):
        """获取已选object对应collection列表"""
        from .utils import get_objects_collection

        selected_objects = context.selected_objects

        obj_coll_list = get_objects_collection(context, selected_objects)
        # 只取其中的collection项
        obj_coll_list = [obj_coll[1] for obj_coll in obj_coll_list]
        return set(obj_coll_list)  # 利用set特性去重


class TEST_PT_selected(sub_Panel):  # 继承基类并实现具体功能
    bl_label = "selected_objects"

    def draw(self, context: Context):
        seleted_objs = context.selected_objects

        layout = self.layout

        for obj in seleted_objs:
            layout.label(text=obj.name)


class TEST_PT_collections(sub_Panel):
    bl_label = "collections"

    def draw(self, context: Context):
        collections = self.get_selected_objects_collection(context)

        layout = self.layout

        # 利用列表解析式执行单行语句
        [layout.label(text=coll.name) for coll in collections]


# 功能面板01
# operator传参方式
class TEST_PT_op01(sub_Panel):
    """把所选对象移至激活对象同collection中"""

    bl_label = "operator01"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: Context):
        active_obj = context.active_object
        seleted_objs = context.selected_objects
        root_collection = context.scene.collection

        # 筛选得到当前激活的object对应colletion
        active_obj_colls = self.get_activeObj_collections(active_obj, root_collection)
        active_obj_coll = active_obj_colls[0]  # 只取第一项,有多个匹配时剩下的会被忽略

        layout = self.layout

        layout.label(text="已选对象:%d" % len(seleted_objs))  # %运算符
        layout.prop(active_obj_coll, "name", text="目标容器")

        op = layout.operator(MoveObjectToCollection.bl_idname)
        # 向operator传递参数
        op.target_name = active_obj_coll.name
        for obj in seleted_objs:
            # CollectionProperty类型使用add()添加并返回该元素
            op.obj_names.add().name = obj.name

    def get_activeObj_collections(self, active_object, root_collection):
        from .utils import nested_object_generator

        return [
            collection
            for collection in nested_object_generator(root_collection, "children")
            if active_object.name in collection.objects
        ]


class Prop_Name_Group(PropertyGroup):  # 自定义参数类型
    name: StringProperty()


class MoveObjectToCollection(Operator):
    """移动对象至容器"""

    bl_idname = "test.move"
    bl_label = "移动至容器"
    bl_options = {"REGISTER", "UNDO"}  # 允许撤销

    # ### prop ### #
    target_name: StringProperty()
    obj_names: CollectionProperty(type=Prop_Name_Group)  # type必须为已注册的property类
    # ### 待传参数 ### #

    def check_erro(self):  # 类型检查
        check = [
            self.target_name == "",
            len(self.obj_names) == 0,
        ]
        return True in check  # 或逻辑

    def execute(self, context: Context):
        from .utils import objects_move_collection

        if self.check_erro():
            return {"CANCELLED"}  # 取消执行

        # 使用传入的名称获取对应实例对象
        data = bpy.data
        objs = [data.objects[item.name] for item in self.obj_names]
        target = (
            context.scene.collection
            if self.target_name == "Master Collection"
            else data.collections[self.target_name]
        )

        objects_move_collection(context, objs, target)
        return {"FINISHED"}


# 功能面板02
# 公共数据管理与动态枚举列表
class TEST_PT_op02(sub_Panel):
    bl_label = "operator02"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: Context):
        seleted_objs = context.selected_objects
        target_name = context.scene.test_enum

        layout = self.layout

        layout.label(text="已选对象:%d" % len(seleted_objs))
        layout.prop(context.scene, "test_enum")  # 储存在scene实例中的自定义数据

        op = layout.operator(MoveObjectToCollection.bl_idname)
        op.target_name = target_name
        for obj in seleted_objs:
            op.obj_names.add().name = obj.name


def enum_items_collection(self, context: Context):  # 动态解析enum枚举回调
    from .utils import filter_current_collections

    collections = filter_current_collections(context)
    return [(x.name, x.name, "") for x in collections]


# ################################# #
# ### END for register function ### #
classes = [
    # base
    TEST_PT_main,
    TEST_PT_selected,
    TEST_PT_collections,
    # op 01
    Prop_Name_Group,
    MoveObjectToCollection,
    TEST_PT_op01,
    # op 02
    TEST_PT_op02,
]


def register():
    [register_class(i) for i in classes]

    # op 02 公共变量储存
    Scene.test_enum = EnumProperty(items=enum_items_collection, name="目标容器")
    # 所有的Scene类实例都会被注入test_enum属性,例 context.scene.test_enum


def unregister():
    [unregister_class(i) for i in classes]


# ################ #
# ### __test__ ### #
if __name__ == "__main__":
    register()
