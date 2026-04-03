"""
DramaForge v2.0 — Projects API
================================
CRUD endpoints for project management.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectList, ProjectDetail

router = APIRouter()


@router.post("/projects", response_model=ProjectDetail, status_code=201)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    project = Project(**body.model_dump())
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


@router.get("/projects", response_model=list[ProjectList])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all projects with pagination."""
    stmt = (
        select(Project)
        .order_by(Project.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/projects/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get project details by ID."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/projects/{project_id}", response_model=ProjectDetail)
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a project."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    await db.flush()
    await db.refresh(project)
    return project


@router.post("/projects/seed-examples", response_model=list[ProjectDetail])
async def seed_example_projects(
    db: AsyncSession = Depends(get_db),
):
    """
    Create example projects with full seed data (scripts, characters, episodes).
    Idempotent: skips if example projects already exist.
    """
    from app.models.script import Script
    from app.models.character import Character
    from app.models.episode import Episode

    # Check if examples already exist
    result = await db.execute(
        select(Project).where(Project.title.like("从弃女到巅峰%"))
    )
    if result.scalar_one_or_none():
        all_result = await db.execute(
            select(Project).order_by(Project.updated_at.desc()).limit(10)
        )
        return all_result.scalars().all()

    # ── Project 1: 从弃女到巅峰 ──
    p1 = Project(
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
    )
    db.add(s1)
    await db.flush()
    await db.refresh(s1)

    for i, (title, content) in enumerate([
        ("订婚宴上的阴谋", "沈念安在订婚宴上被继妹沈薇薇下药陷害，当众出丑..."),
        ("三年后的归来", "三年后，沈念安以全新身份回到A市，携手顾承泽开始复仇计划..."),
        ("步步为营", "沈念安利用商业手段逐步瓦解继母周助理的势力..."),
        ("真相大白", "关键证据浮出水面，当年的阴谋被完全揭开..."),
        ("巅峰对决", "最终对决，沈念安夺回属于自己的一切，家族回归正轨..."),
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


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a project and all related data."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.flush()
