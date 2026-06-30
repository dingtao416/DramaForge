"""
DramaForge v2.0 — Projects API
================================
CRUD endpoints for project management.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.project import Project
from app.models.script import Script
from app.models.episode import Episode
from app.models.character import Character
from app.models.scene import SceneLocation
from app.models.segment import Segment
from app.models.user import Conversation
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectList, ProjectDetail
from app.core.security import CurrentUser, get_user_project
from app.services.storage import storage
from app.services.storyboard_generation_service import cleanup_project_storyboard_progress
from app.tasks.asset_tasks import cancel_project_asset_tasks
from app.tasks.video_tasks import cancel_project_video_tasks
from app.api.v2.scripts import cancel_project_script_generation

router = APIRouter()


@router.post("/projects", response_model=ProjectDetail, status_code=201)
async def create_project(
    body: ProjectCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    project = Project(user_id=user.id, **body.model_dump())
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


@router.get("/projects", response_model=list[ProjectList])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    """List all projects for the current user with pagination."""
    stmt = (
        select(Project)
        .where(Project.user_id == user.id)
        .order_by(Project.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/projects/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get project details by ID."""
    return await get_user_project(project_id, user, db)


@router.put("/projects/{project_id}", response_model=ProjectDetail)
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Update a project."""
    project = await get_user_project(project_id, user, db)

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    await db.flush()
    await db.refresh(project)
    return project


@router.post("/projects/seed-examples", response_model=list[ProjectDetail])
async def seed_example_projects(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Create example projects with full seed data (scripts, characters, episodes).
    Idempotent: skips if example projects already exist for this user.
    """
    from app.models.script import Script
    from app.models.character import Character
    from app.models.episode import Episode

    # Check if examples already exist for this user
    result = await db.execute(
        select(Project).where(
            Project.title.like("从弃女到巅峰%"),
            Project.user_id == user.id,
        )
    )
    if result.scalar_one_or_none():
        all_result = await db.execute(
            select(Project)
            .where(Project.user_id == user.id)
            .order_by(Project.updated_at.desc())
            .limit(10)
        )
        return all_result.scalars().all()

    # ── Project 1: 从弃女到巅峰 ──
    p1 = Project(
        user_id=user.id,
        title="从弃女到巅峰：苏家千金归来",
        description="苏家千金被陷害沦为弃女，凭借智慧与毅力一步步重回巅峰。",
        style="realistic", genre="revenge", status="storyboard",
        script_type="dialogue", aspect_ratio="9:16",
    )
    db.add(p1)
    await db.flush()
    await db.refresh(p1)

    s1 = Script(
        project_id=p1.id, protagonist="沈念安", genre="女频",
        synopsis="[地位反差/身份错位 豪门养女沈念安在订婚宴上，被亲生女儿妹妹当众揭发未婚夫出轨并怀孕，随后被养父母揭穿养女身份并被当作弃子逐出家门，从云端跌落尘埃。]",
        background="现代，现代都市。主要场景包括豪华酒店宴会厅、沈家、念安设计工作室、豪华公寓。",
        setting="主角沈念安被神秘人所救，条件是必须隐姓埋名，以\"安宁\"的新身份生活，为复仇做准备。",
        one_liner="在自己盛大的订婚宴上，设计师沈念安的人生从云端坠入深渊。她满心欢喜地准备与未婚夫顾承泽开启新生活，却被亲妹妹沈薇薇当众揭露——她已怀上顾承泽的孩子。这场突如其来的背叛，只是她噩梦的开始。",
        is_approved=True,
        # ── Story Bible ──
        premise="这是一部都市复仇题材的短剧，讲述豪门养女沈念安在订婚宴上遭养妹沈薇薇和未婚夫顾承泽联手背叛，被养父母揭穿身份逐出家门后，凭设计天赋和商业头脑逆袭归来的故事。核心矛盾是'亲情vs利益'和'真相vs谎言'——沈家以血缘之名行抛弃之实，沈念安以实力证明价值不以血缘定义。主题：真正的家人不是血脉相连，而是在你最黑暗时仍然站在你身边的人。",
        world_rules="故事发生在当代都市A市，以上流社会商圈为核心舞台。世界的运行规则是'利益为王'：沈家作为A市豪门，家族企业沈氏集团是核心权力来源；人物阶层分明——豪门千金/少爷、白领精英、普通市民。关键设定：① 沈念安的养女身份是沈家最大的秘密，仅有沈父沈母和少数核心知情人知晓；② 设计工作室是沈念安的核心竞争力，也是她逆袭的物理基石；③ 网络舆论是双刃剑，既可以摧毁一个人也能重塑一个人。",
        character_relationships="沈念安↔沈薇薇：养姐妹→仇敌。沈薇薇嫉妒沈念安的才华和顾承泽的偏爱，设计夺走顾承泽并嫁祸沈念安。\n沈念安↔顾承泽：未婚夫妻→仇敌→复杂。顾承泽被沈薇薇的手段所蒙蔽，后逐渐发现真相但已无法回头。\n沈念安↔沈母：养母女→决裂。沈母在家族利益和养女之间选择了前者，当着宾客的面揭露养女身份。\n沈念安↔周助理（继母）：敌对。周助理是沈薇薇幕后最大的推手，掌控沈氏财务暗中转移资产。\n沈念安↔神秘救星：救助→盟友。三年前被赶出沈家时伸出援手的神秘人，身份贯穿全剧悬念。",
        timeline="第0年（开篇）：订婚宴阴谋——沈念安被下药陷害，养女身份揭穿，被赶出沈家。\n第3年（现在）：三年后归来——沈念安以设计师'安宁'的全新身份回到A市，已拥有一间小有名气的设计工作室。\n第1-2集：初次交锋——在商业场合偶遇沈家人，沈薇薇未认出她但感到莫名威胁。\n第3-4集：商业围剿——沈念安利用商业合同陷阱逐步瓦解沈氏的关键客户关系。\n第5集：真相大白→巅峰对决——三年前的录音证据被公开，沈家内部分裂，沈念安夺回属于自己的一切。",
        episode_arc="第1集（开篇钩子）：订婚宴惊变→身份被揭穿→被赶出家门，以沈念安在暴雨中被神秘人救起为结尾钩子。爽点：身份的极端反转。\n第2集（三年后）：沈念安以设计师安宁的全新身份登场，已完成蜕变——冷静、自信、强大。在商业酒会上与沈薇薇首次正面相遇。爽点：王者归来的气场碾压。\n第3集（商业反击）：沈念安利用合同陷阱让沈氏损失重要客户，沈薇薇开始怀疑安宁的真实身份。爽点：智力碾压+身份悬念。\n第4集（联盟建立/回忆闪回）：揭示三年前神秘救星的真实身份——某商业集团少董。沈念安与少董结盟，同时沈薇薇开始疯狂反扑。爽点：情感共鸣+联盟建立。\n第5集（终局对决）：三年前的录音和监控证据被公之于众，沈氏股价暴跌，沈家内部分裂。沈念安在新闻发布会上面纱揭下，回归真名。爽点：真相揭示+名字回归，情感高潮。",
        visual_style_rules="色调：以冷色调为主（蓝灰、深蓝、银色基调），穿插暖色对比（回忆片段使用温暖的金黄色调，象征过去的美好；复仇场景使用高对比度的冷色+暗红色点缀，象征危机中的力量）。\n光影：内景使用硬光和高对比度营造紧张感，外景使用柔光和散景营造都市感。\n镜头语言：拍沈念安时多用低角度仰拍+稳定构图，暗示她的力量和坚韧；拍沈薇薇时多用略俯拍+轻微晃动，暗示内心的不安和嫉妒。\n转场风格：时间跳跃使用硬切+对比色卡，回忆使用柔化过渡+暖色滤镜，情绪转换使用匹配剪辑。",
        continuity_notes="沈念安的标志性配饰——一条银色细链项链（生母留下的遗物），必须在所有重要场景中佩戴。第1集被赶出沈家时项链被扯断，第2集归来时项链已修复但留有一处不易察觉的焊接痕迹。\n沈念安的设计工作室名称'念安设计'在第2-5集中需要保持一致的招牌外观（白色亚克力字+暖光背灯）。\n沈薇薇的左眉尾端有一道细小疤痕（第1集被摔碎的玻璃杯划伤），后期化妆风格应始终保持能遮住但偶尔能看到的程度。\n时间线标记：第2-5集剧情发生在一年之内（秋冬→来年秋季），服装需按季节变化。"
    )
    db.add(s1)
    await db.flush()
    await db.refresh(s1)

    for i, (title, content) in enumerate([
        ("订婚惊变妹妹夺爱", "△ （全景）豪华酒店宴会厅内，水晶吊灯璀璨夺目，鲜花簇拥的主席台上司仪正调试话筒。台下宾客云集，沈家千金的订婚宴即将开始。\n\n**司仪**（激昂）:\"今天，是沈家千金沈念安与顾家公子顾承泽的订婚宴。\"\n\n△ （近景）沈念安身着一袭香槟色礼服站在台侧，手指不自觉地摩挲着颈间的银色细链项链，眼中满是期待。\n\n**沈薇薇**（甜美，举杯起身）:\"等一下！姐姐，我有话要说。\"\n\n△ （中景）沈薇薇缓缓站起，嘴角挂着完美的笑容，眼神却冰冷如刃。\n\n**沈薇薇**:\"我怀孕了。孩子是……承泽的。\"\n\n♪ 尖锐的弦乐戛然而止\n\n△ （大特写）沈念安的手指死死攥住项链，链子深深陷入掌心。\n\n> 🎣 本集钩子：沈念安被揭穿养女身份，沈母当众说出\"她不是我的女儿\"\n> 📺 下集预告：被赶出家门的沈念安在暴雨中遇神秘人相救，三条件交换改变她的一生"),
        ("三年后华丽归来", "△ （航拍）A市CBD的清晨，阳光穿过摩天大楼映照在'念安设计'工作室的白底招牌上，暖光背灯柔和发光。\n\n△ （中景）沈念安——不，现在她叫安宁——站在落地窗前俯视城市轮廓。剪裁完美的黑色西装，银色项链已修复但隐约可见焊接痕迹。她的眼神比三年前冷了许多。\n\n**安宁**（平静的电话）:\"沈氏的合同漏洞我已经标注好了，重点看第十一条滞纳金条款。\"\n\n△ （全景）商业酒会现场。沈薇薇挽着顾承泽的手臂穿梭于宾客间，笑容灿烂。她的目光落在角落里独自品酒的安宁身上，微微皱眉——这个女人的侧脸，有几分眼熟。\n\n♪ 奢华的弦乐背景下，低沉的电子音效隐隐浮现\n\n**沈薇薇**（优雅走近）:\"这位女士，我们是不是在哪里见过？\"\n\n**安宁**（转身，完美的职业微笑）:\"恐怕没有。我是新来的设计师，安宁。\"\n\n△ （特写）沈念安颈间的项链在灯光下微微闪烁。沈薇薇的瞳孔几不可察地收缩了一下。\n\n> 🎣 本集钩子：沈薇薇在安宁的颈间看到了那条似曾相识的项链\n> 📺 下集预告：沈氏最重要的大客户被神秘对手截胡，安宁的商业才华首次展现"),
        ("致命合同步步为营", "△ （俯拍）沈氏集团会议室。沈父面色铁青地摔下手中的合同，纸张散落在会议桌上。\n\n**沈父**（压抑怒火）:\"郑氏集团和我们合作了十五年！十五年！谁告诉我这个'念安设计'是从哪里冒出来的？！\"\n\n△ （中景）沈薇薇咬着下唇翻阅平板上的数据，脸色苍白。屏幕上是念安设计工作室的官网首页——极简风格，实力展示令人窒息的专业度。\n\n△ （特写）安宁的手指在平板上轻敲，调出一张沈氏集团的财务流向图。她身边的少董——那个三年前在暴雨中开车经过的神秘人——递给她一杯咖啡。\n\n**少董**（似笑非笑）:\"你已经盯了他们半个月了。准备什么时候摘下面纱？\"\n\n**安宁**:\"不急。让她们先恐慌。恐慌中的人才最容易被自己的贪婪吞噬。\"\n\n△ （镜头切换）沈氏集团停车场。沈薇薇的助理周助理——实际上是她继母——正对着手机压低声音。\n\n**周助理**（低语）:\"安宁·沈……查她的背景。三年前，A市有没有姓沈的设计师？\"\n\n♪ 紧张的电子节拍逐渐升高\n\n> 🎣 本集钩子：周助理在旧报纸上翻到了三年前沈念安订婚宴的照片\n> 📺 下集预告：三年前的秘密浮出水面，少董的身份被揭晓——他不是普通的商业伙伴"),
        ("三年前的秘密浮出水面", "△ （移动镜头）沈念安站在沈氏集团楼下仰望着熟悉又陌生的玻璃大楼。阳光刺眼，她抬手遮挡——手腕上的设计腕表反射出一道锐利的光。\n\n**少董**:\"需要我陪你上去吗？\"\n\n**安宁**（嘴角微扬）:\"这次，我要一个人走进去。\"\n\n△ （全景）沈氏集团紧急董事会。投影仪上正播放着一段三年前的录音——沈薇薇和周助理的对话：\"只要把药放进她的酒杯，我就怀孕说她陷害我，爸爸一定会把她赶出去的……\"\n\n△ （近景）沈薇薇的指甲陷进皮椅扶手，脸色灰白。沈母捂住了嘴，眼泪无声滑落。沈父的脸从青转白，手边的茶杯随着他的颤抖发出细微的碰撞声。\n\n**沈父**（苍老了许多）:\"这……这不是真的……\"\n\n△ （大特写）会议室大门被推开。逆光中，一个剪影缓缓步入——是安宁，穿着和订婚宴上同一件香槟色礼服，颈间项链已换成崭新却同款的银色细链。\n\n**安宁**（温柔而坚定）:\"三年前，你们说我不是沈家的女儿。三年后，我回来，不是为了讨回身份。而是来告诉你们——我做沈念安，比做沈家的女儿更好。\"\n\n♪ 大提琴低沉的旋律突然升调，弦乐群齐奏\n\n> 🎣 本集钩子：沈父突发心梗倒地，沈氏股价暴跌无人掌舵\n> 📺 下集预告：家族终局抉择——沈念安面临最艰难的选择：拯救还是摧毁"),
        ("巅峰对决重掌人生", "△ （航拍）A市黄昏，夕阳将天际染成金红色。沈氏集团总部顶层办公室。\n\n△ （中景）沈父躺在病床上通过视频连线参与最后的决定。沈母坐在角落，苍老了十岁的模样，紧紧攥着三年前那张订婚宴的老照片。\n\n△ （近景）沈薇薇站在办公室中央，周围是空荡荡的座椅——曾经围绕她的拥护者都已离去。她的左眉尾端，那处不起眼的疤痕此刻异常显眼。\n\n**沈薇薇**（歇斯底里）:\"你赢了好不好？！你拿回去吧——所有的一切！沈家，公司，全部！\"\n\n**安宁**（冷静）:\"我不需要沈家。我已经有自己的家了。\"\n\n△ （全景）新闻发布会现场。镁光灯此起彼伏。安宁——不，沈念安——站在'念安设计'的logo前，少董站在她身侧。\n\n**沈念安**（摘下面纱，看向镜头）:\"大家好。三年前我叫沈念安。今天，我不再需要用'安宁'来保护自己。因为我发现——让我变强的，从来不是复仇。而是成为我自己。\"\n\n△ （特写）她抬手，轻轻触碰颈间那条崭新的银色项链。\n\n♪ 从低沉的电子音效渐变为温暖的钢琴旋律\n\n△ （拉远全景）A市的华灯初上。沈念安的设计工作室里透出暖黄色的光。窗边，她翻开一沓新的设计稿，第一页写着：\n\n\"献给所有跌入深渊却从未放弃的女孩。\"\n\n> 📺 全剧终"),
    ], 1):
        db.add(Episode(script_id=s1.id, number=i, title=title, content=content, is_approved=True))

    p1_img_base = "/storage/seed_images/project1"
    p1_char_data = [
        ("沈念安", "protagonist", f"{p1_img_base}/shen_nianan.jpg"),
        ("沈母", "supporting", f"{p1_img_base}/shen_mu.jpg"),
        ("顾承泽", "supporting", f"{p1_img_base}/gu_chengze.jpg"),
        ("沈薇薇", "antagonist", f"{p1_img_base}/shen_weiwei.jpg"),
        ("沈父", "supporting", f"{p1_img_base}/shen_fu.jpg"),
        ("周助理", "antagonist", f"{p1_img_base}/zhou_zhuli.jpg"),
        ("宾客甲", "extra", f"{p1_img_base}/binke_jia.jpg"),
        ("宾客乙", "extra", f"{p1_img_base}/binke_yi.jpg"),
        ("保安", "extra", f"{p1_img_base}/baoan.jpg"),
        ("先生", "extra", f"{p1_img_base}/xiansheng.jpg"),
        ("司仪", "extra", f"{p1_img_base}/siyi.jpg"),
    ]
    for name, role, img in p1_char_data:
        db.add(Character(project_id=p1.id, name=name, role=role, reference_images=[img]))

    # ── Project 2: 末世 ──
    p2 = Project(
        user_id=user.id,
        title="末世：我以为我是废柴，其实我是神",
        description="末世来临，被所有人看不起的废柴觉醒了最强能力。",
        style="cinematic", genre="fantasy", status="storyboard",
        script_type="dialogue", aspect_ratio="9:16",
    )
    db.add(p2)
    await db.flush()
    await db.refresh(p2)

    s2 = Script(
        project_id=p2.id, protagonist="林萧", genre="男频",
        synopsis='被基地众人视为"废柴"的林萧，唯一的念头就是拾荒为重病的妹妹小雨换取救命药。当B级异兽来袭，林萧在绝境中觉醒SSS级异能"力量增幅"，单手挡下龙爪。',
        background="末日/后启示录时代，末日废土世界中的人类基地及其周边废墟。",
        setting='异兽横行: 世界被各种等级的"异兽"侵占。\n异能等级: 人类中存在"异能者"，拥有明确的实力等级划分。\n基地社会: 幸存的人类聚集在"基地"中生活。\n系统存在: 主角林萧是"宿主"，其经历的一切都只是"系统"设定的"第一阶段试炼"。',
        one_liner='被基地众人视为"废柴"的林萧，在末世中觉醒最强异能，揭开系统试炼的惊天真相。',
        is_approved=True,
    )
    db.add(s2)
    await db.flush()
    await db.refresh(s2)

    for i, (title, content) in enumerate([
        ("废柴逆袭 兽王降临", "林萧在基地被众人嘲笑为废柴，B级异兽来袭时他觉醒了异能..."),
        ("徒手撼龙爪", "林萧面对SSS级兽王，徒手挡下龙爪，震惊基地所有人..."),
        ("潜龙出渊 一拳撼天", "林萧的实力不断增长，开始主动出击清剿附近异兽群落..."),
        ("战神觉醒 金光化身", "真正的危机降临，林萧觉醒完全体异能，化身金光战神..."),
        ("斩龙之剑 末世序章", "林萧击败最终BOSS后系统声音响起，揭示一切不过是试炼的开始..."),
    ], 1):
        db.add(Episode(script_id=s2.id, number=i, title=title, content=content, is_approved=True))

    for name, role in [
        ("林萧", "protagonist"), ("王强", "supporting"), ("苏晴", "supporting"),
        ("黑龙", "antagonist"), ("林萧的妹妹", "supporting"), ("系统音", "supporting"),
    ]:
        db.add(Character(project_id=p2.id, name=name, role=role, reference_images=[]))

    # ── Project 3: 都市大圣 ──
    p3 = Project(
        user_id=user.id,
        title="都市大圣：战神觉醒",
        description="退伍战神重回都市，以雷霆手段守护至亲。",
        style="realistic", genre="urban", status="script",
        script_type="dialogue", aspect_ratio="9:16",
    )
    db.add(p3)
    await db.flush()
    await db.refresh(p3)

    s3 = Script(
        project_id=p3.id, protagonist="陈锋", genre="都市",
        synopsis="五年前被迫离开家族的陈锋，以退伍战神的身份重回都市。面对家族内部的背叛和商业对手的围堵，他以雷霆手段一一化解危机。",
        background="现代繁华都市，陈氏集团总部大楼。",
        setting="陈锋是陈氏集团创始人之孙，五年前被叔父陈坤设计逐出家族。他在军中历练五年，成为特种部队王牌。如今爷爷病重，他带着秘密身份回归。",
        one_liner="退伍战神回归都市，拨开重重阴谋夺回家族。",
        is_approved=True,
    )
    db.add(s3)
    await db.flush()
    await db.refresh(s3)

    for i, (title, content) in enumerate([
        ("战神归来", "退伍战神陈锋回到都市，发现家族早已被叔父架空..."),
        ("暗流涌动", "陈锋开始暗中调查叔父的阴谋，发现惊天秘密..."),
        ("绝地反击", "陈锋利用军中人脉和商业智慧发起反击..."),
        ("最终审判", "真相浮出水面，陈锋在董事会上揭露一切..."),
        ("新的开始", "家族重归正轨，陈锋找到属于自己的归宿..."),
    ], 1):
        db.add(Episode(script_id=s3.id, number=i, title=title, content=content, is_approved=True))

    for name, role in [
        ("陈锋", "protagonist"), ("陈坤", "antagonist"), ("林婉儿", "supporting"),
        ("陈老爷子", "supporting"), ("赵秘书", "supporting"),
    ]:
        db.add(Character(project_id=p3.id, name=name, role=role, reference_images=[]))

    await db.flush()
    return [p1, p2, p3]


@router.post("/projects/{project_id}/duplicate", response_model=ProjectDetail, status_code=201)
async def duplicate_project(
    project_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Duplicate a project with its script, episodes, characters, and scenes.
    Does NOT copy segments/shots (video generation data)."""
    src = await get_user_project(project_id, user, db)

    # Create new project
    new_project = Project(
        user_id=user.id,
        title=f"{src.title}（副本）",
        description=src.description,
        style=src.style,
        aspect_ratio=src.aspect_ratio,
        genre=src.genre,
        status="script",  # Reset to script step
        script_type=src.script_type,
    )
    db.add(new_project)
    await db.flush()
    await db.refresh(new_project)

    # Copy script
    script_stmt = select(Script).where(Script.project_id == project_id).options(selectinload(Script.episodes))
    script_result = await db.execute(script_stmt)
    src_script = script_result.scalar_one_or_none()

    if src_script:
        new_script = Script(
            project_id=new_project.id,
            protagonist=src_script.protagonist,
            genre=src_script.genre,
            synopsis=src_script.synopsis,
            background=src_script.background,
            setting=src_script.setting,
            one_liner=src_script.one_liner,
            raw_content=src_script.raw_content,
            premise=src_script.premise,
            world_rules=src_script.world_rules,
            character_relationships=src_script.character_relationships,
            timeline=src_script.timeline,
            episode_arc=src_script.episode_arc,
            visual_style_rules=src_script.visual_style_rules,
            continuity_notes=src_script.continuity_notes,
        )
        db.add(new_script)
        await db.flush()

        # Copy episodes (without segments/shots)
        for ep in src_script.episodes:
            new_ep = Episode(
                script_id=new_script.id,
                number=ep.number,
                title=ep.title,
                content=ep.content,
            )
            db.add(new_ep)

    # Copy characters
    char_stmt = select(Character).where(Character.project_id == project_id)
    char_result = await db.execute(char_stmt)
    for ch in char_result.scalars().all():
        new_ch = Character(
            project_id=new_project.id,
            name=ch.name,
            role=ch.role,
            description=ch.description,
            voice_desc=ch.voice_desc,
            reference_images=list(ch.reference_images or []),
        )
        db.add(new_ch)

    # Copy scenes
    scene_stmt = select(SceneLocation).where(SceneLocation.project_id == project_id)
    scene_result = await db.execute(scene_stmt)
    for sc in scene_result.scalars().all():
        new_sc = SceneLocation(
            project_id=new_project.id,
            name=sc.name,
            description=sc.description,
            time_of_day=sc.time_of_day,
            interior=sc.interior,
            reference_images=list(sc.reference_images or []),
        )
        db.add(new_sc)

    await db.flush()
    await db.refresh(new_project)
    return new_project


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Delete a project and all related data."""
    project = await get_user_project(project_id, user, db)

    episode_result = await db.execute(
        select(Episode.id)
        .join(Script, Episode.script_id == Script.id)
        .where(Script.project_id == project_id)
    )
    episode_ids = list(episode_result.scalars().all())

    segment_result = await db.execute(
        select(Segment.id)
        .join(Episode, Segment.episode_id == Episode.id)
        .join(Script, Episode.script_id == Script.id)
        .where(Script.project_id == project_id)
    )
    segment_ids = list(segment_result.scalars().all())

    character_result = await db.execute(
        select(Character.id).where(Character.project_id == project_id)
    )
    character_ids = list(character_result.scalars().all())

    conversation_result = await db.execute(
        select(Conversation).where(
            Conversation.project_id == project_id,
            Conversation.user_id == user.id,
        )
    )
    conversations = list(conversation_result.scalars().all())

    cancel_project_script_generation(project_id)
    cancel_project_asset_tasks(project_id, character_ids)
    cancel_project_video_tasks(segment_ids, episode_ids)
    await cleanup_project_storyboard_progress(project_id, user.id, episode_ids)

    for conversation in conversations:
        await db.delete(conversation)

    await db.delete(project)
    await db.flush()
    storage.delete_project_tree(project_id)
