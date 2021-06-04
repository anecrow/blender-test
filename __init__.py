#######################
# ### bpy imports ### #
import bpy
from bpy.utils import register_class, unregister_class

# ### base class ### #
from bpy.types import Operator, Panel, Context
from bpy.types import Collection

# ### prop types ### #
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty

# ### prop group ### #
from bpy.types import PropertyGroup, Scene, PointerProperty


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


class TEST_PT_selected(sub_Panel):
    bl_label = "selected_objects"

    @classmethod
    def poll(cls, context):  # 检查函数
        seleted_objs = context.selected_objects
        check = len(seleted_objs) > 0
        return check  # 返回值为空(含False)时,阻止本类实执行和实例化

    def draw(self, context: Context):
        seleted_objs = context.selected_objects

        layout = self.layout

        for obj in seleted_objs:
            layout.label(text=obj.name)


class TEST_PT_collections(sub_Panel):
    bl_label = "collections"

    # 静态函数/类函数,第一个参数指向类本身
    @classmethod  # 静态函数装饰器
    def poll(cls, context):
        seleted_objs = context.selected_objects
        check = len(seleted_objs) > 0
        return check

    # 实例函数,实例化前不可用,第一个参数指向类实例
    def draw(self, context: Context):
        seleted_objs = context.selected_objects
        collections = context.scene.collection.children
        colls = self.get_objects_collections(seleted_objs, collections)  # 调用实例函数

        layout = self.layout

        for coll in colls:
            layout.label(text=coll.name)

    def get_objects_collections(self, objects, collections):
        colls = []
        for coll in collections:
            for obj in objects:
                if obj.name in coll.objects:
                    colls.append(coll)
                    break  # 跳出本级循环,将跳过后续遍历,但不影响上级遍历
        return colls

    def get_objects_collections_02(self, objects, collections):
        return set(  # 利用Set类型特性去重
            [  # 列表生成式,别问有什么用,问就是优雅漂亮
                coll.name  # 元素语句
                for coll in collections  # 第一层遍历
                for obj in objects  # 第二层遍历
                if obj.name in coll.objects  # 筛选语句,为True时将元素语句添加进列表中
            ]
        )


# 功能面板01
# operator传参方式
class TEST_PT_op01(sub_Panel):
    bl_label = "operator01"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        seleted_objs = context.selected_objects
        check = len(seleted_objs) > 0
        return check

    def draw(self, context: Context):
        active_obj = context.active_object
        seleted_objs = context.selected_objects
        collections = (
            context.scene.collection.children
        )  # TODO: 仅工作于根collection,内部套嵌对象不可用

        layout = self.layout

        _layout = layout.column()
        _layout.enabled = False  # disable效果
        _layout.label(text="把所选对象移至激活对象同collection中")

        target = self.get_obj_collection(active_obj, collections)
        layout.label(text="已选对象:%d" % len(seleted_objs))  # %运算符
        layout.prop(target, "name", text="目标容器")

        op = layout.operator(MoveObjectToCollection.bl_idname)
        # 向operator传递参数
        op.target_name = target.name
        for obj in seleted_objs:
            # CollectionProperty类型使用add()添加并返回该元素
            op.obj_names.add().name = obj.name

    def get_obj_collection(self, object, collections):
        return [x for x in collections if object.name in x.objects][0]
        # 返回第一个匹配到的collection,其他将被忽略
        # for collection in collections:
        #     if object.name in collection.objects:
        #         return collection


class Prop_Name_Group(PropertyGroup):
    name: StringProperty()


# TODO: link 和 unlink 方法可拆分为通用util函数
class MoveObjectToCollection(Operator):
    """移动对象至容器"""

    bl_idname = "test.move"
    bl_label = "移动至容器"

    # ### prop ### #
    target_name: StringProperty()
    obj_names: CollectionProperty(type=Prop_Name_Group)  # type必须为已注册的property类
    # ### 待传参数 ### #

    def execute(self, context: Context):
        # 类型检查
        check = [
            self.target_name == "",
            len(self.obj_names) == 0,
        ]
        if True in check:
            return {"CANCELLED"}

        data = bpy.data
        collection = data.collections[self.target_name]
        objs = [data.objects[item.name] for item in self.obj_names]

        [
            collection.objects.link(obj)  # 利用列表生成式遍历执行添加任务
            for obj in objs
            if obj.name not in collection.objects
        ]
        self.unlink_other_collections(data.collections, objs)  # 清除原链接关系
        return {"FINISHED"}

    def unlink_other_collections(self, collections, objects):
        # 建立容器对应列表
        task = [
            (collection, object)
            for collection in collections
            for object in objects
            if object.name in collection.objects
        ]
        print(task)

        # 清除非目标容器内的对象
        name = self.target_name
        [x[0].objects.unlink(x[1]) for x in task if x[0].name != name]
        # 等效于
        # def unlink(collection, object):
        #     collection.objects.unlink(object)

        # for item in task:
        #     if item[0].name != self.target_name:
        #         unlink(item[0], item[1])


# 功能面板02
# 公共数据管理与动态枚举列表
class TEST_PT_op02(sub_Panel):
    bl_label = "operator02"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        seleted_objs = context.selected_objects
        check = len(seleted_objs) > 0
        return check

    def draw(self, context: Context):
        seleted_objs = context.selected_objects

        layout = self.layout

        layout.label(text="已选对象:%d" % len(seleted_objs))
        layout.prop(context.scene, "test_enum")

        op = layout.operator(MoveObjectToCollection.bl_idname)
        op.target_name = context.scene.test_enum
        for obj in seleted_objs:
            op.obj_names.add().name = obj.name


def enum_items_collection(self, context: Context):  # 动态解析enum枚举项
    # 迭代函数
    def get_all_children(collection: Collection, collections: list = []):
        for item in collection.children:
            if item in collections:
                continue  # 防止循环套嵌
            collections.append(item)
            get_all_children(item, collections)
        return collections

    collection = context.scene.collection  # 根容器
    collections = get_all_children(collection, [collection])  # 自身和所有子代集合

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
    bpy.types.Scene.test_enum = EnumProperty(items=enum_items_collection, name="目标容器")
    # 所有的Scene类实例都会被注入test_enum属性,例 context.scene.test_enum


def unregister():
    [unregister_class(i) for i in classes]


# ################ #
# ### __test__ ### #
if __name__ == "__main__":
    register()
