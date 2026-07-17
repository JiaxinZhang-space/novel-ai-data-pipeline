"""Generate deterministic synthetic stories and intentional data-quality defects."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .constants import DEMO_MARKER


NAMES = [
    "沈照月",
    "顾南枝",
    "程晚星",
    "陆青禾",
    "苏见微",
    "林砚秋",
    "许昭宁",
    "江予棠",
    "叶知澜",
    "温如霜",
    "唐映雪",
    "周明玥",
    "秦望舒",
    "宋栖云",
    "谢沉璧",
    "傅清嘉",
    "黎初夏",
    "楚怀音",
    "贺兰溪",
    "孟疏影",
]

CITIES = ["临川", "云州", "海陵", "北辰", "雁城", "青港", "锦宁", "安澜", "澄江", "望京"]

PROFESSIONS = [
    "非遗修复师",
    "急诊医生",
    "供应链审计师",
    "纪录片导演",
    "新能源工程师",
    "刑事律师",
    "独立书店主理人",
    "水利工程师",
    "游戏制作人",
    "文物鉴定师",
    "食品安全调查员",
    "建筑设计师",
    "数据取证专家",
    "海洋生物研究员",
    "舞台灯光师",
    "社区规划师",
    "航空维修工程师",
    "田野记者",
    "应急救援队长",
    "知识产权顾问",
]

OBJECTS = [
    "一册被调换页码的古籍",
    "一份被隐藏的急诊交接记录",
    "一组异常仓储温度曲线",
    "一段被剪掉七秒的原始影像",
    "一枚来源不明的控制芯片",
    "一封没有进入卷宗的证人邮件",
    "一本夹着旧车票的绝版书",
    "一张被重画的河道勘测图",
    "一份被覆盖的版本提交记录",
    "一只带有修补痕迹的青铜匣",
    "一批检测编号连续跳号的样品",
    "一套被悄悄改变承重参数的图纸",
    "一块时间戳矛盾的加密硬盘",
    "一份被删去坐标的海洋观测日志",
    "一张比演出提前亮起的灯位表",
    "一份绕开听证程序的更新方案",
    "一枚重复登记的发动机零件",
    "一段被匿名账号撤回的采访录音",
    "一张标注错误集合点的救援地图",
    "一份授权范围被后补修改的合同",
]

CONFLICTS = [
    "家族工坊将事故推给临时学徒",
    "科室负责人要求她删除关键时间点",
    "合作方用低价供应商替换安全材料",
    "投资人要求她把受访者改成反派",
    "项目经理打算在验收前掩盖故障",
    "明星委托人要求她牺牲无辜证人",
    "连锁资本逼迫老街商户提前退租",
    "开发商试图把洪水风险转嫁给下游村镇",
    "发行方要求团队复制竞品并删掉署名",
    "收藏集团用舆论否定她的鉴定结果",
    "地方品牌准备把污染责任推给小作坊",
    "甲方要求她为赶工删除抗震复核",
    "平台安全负责人阻止她追查内部账号",
    "企业赞助方要求研究结论避开污染源",
    "制作人用演员安全换取直播热度",
    "地产集团借更新名义驱赶原住民",
    "承包商要求她在故障单上签署误操作",
    "公关团队要求她撤回工伤调查报道",
    "商业活动占用了唯一的应急通道",
    "客户要求她用模糊条款夺走青年作者版权",
]

ALLIES = [
    "寡言的档案管理员",
    "坚持复核的年轻护士",
    "熟悉冷库设备的夜班工人",
    "保存母带的剪辑助理",
    "被边缘化的测试工程师",
    "拒绝改口的实习调查员",
    "每天记录客流的咖啡店老板",
    "会看旧水文碑的退休教师",
    "维护开源工具的匿名玩家",
    "熟悉锈层的老铸工",
    "保留送检小票的摊主",
    "关注无障碍设计的实习生",
    "写下值班日志的机房保安",
    "长期巡海的渔船船长",
    "记得每次彩排的替补演员",
    "组织口述史的社区志愿者",
    "坚持拍照留档的检修员",
    "保存采访笔记的摄影记者",
    "熟悉山路的民间救援者",
    "拒绝出售署名权的新人作者",
]

REVERSALS = [
    "她发现所谓失误其实来自一套重复使用多年的调包流程",
    "她证明被责怪的新人反而是唯一按流程操作的人",
    "她查到对方制造的时间差正好暴露了审批者",
    "她意识到最体面的公开声明就是掩盖证据的脚本",
    "她确认故障并非偶发，而是人为关闭报警后的必然结果",
    "她找到一项足以推翻委托人叙事的旧判例",
    "她发现收购计划依赖一份从未获得居民同意的测绘报告",
    "她把百年水痕与最新模型叠加，证明风险被系统性低估",
    "她发现抄袭指令来自最强调原创的高层",
    "她证明真品上的修补恰恰记录了被抹去的女性工匠",
    "她把检测批次与运输路线对齐，锁定了真正的污染环节",
    "她发现删去的复核项曾在另一座建筑中避免过事故",
    "她还原硬盘后发现攻击账号属于内部白名单",
    "她将潮汐和排放时刻重合，证明异常并非自然波动",
    "她调出备用控台日志，发现事故预案被人为锁定",
    "她证明所谓空置率来自人为停水停电",
    "她在零件履历中发现同一编号经历了三次报废重生",
    "她发现匿名爆料人正是被报道企业的基层女工",
    "她还原路线后确认拥堵来自未经备案的商业围栏",
    "她对比合同元数据，证明新增条款晚于双方签署时间",
]

RESOLUTIONS = [
    "公开修复日志并成立学徒共同署名制度",
    "保全原始记录并推动医院重建交接审计",
    "暂停出货、召回产品并建立供应商追踪台账",
    "交出未经剪辑的证据，让受访者保有自己的叙述权",
    "让项目延期复检，并把报警配置纳入不可绕过的门禁",
    "解除代理关系，保护证人并促成重新调查",
    "用社区合作社保住街区经营权",
    "启动泄洪整改并让风险数据向居民公开",
    "带领核心成员独立发布原创版本",
    "把无名工匠写回展签和研究档案",
    "完成全链路召回并建立公开检测编号",
    "拒绝盖章并推动第三方结构复核",
    "冻结问题权限并建立独立取证链",
    "公开可复现实验，迫使污染方接受长期监测",
    "中止直播并重建演员安全确认流程",
    "以居民档案和法律程序阻止强制搬迁",
    "拒绝虚假签字并推动适航复检",
    "发布完整证据链并为爆料人提供匿名保护",
    "拆除违规围栏并重绘多语言救援路线",
    "终止不公代理并帮助作者追回数字版权",
]


def _rights(author_index: int) -> dict[str, Any]:
    return {
        "contract_id": f"DEMO-CONTRACT-{author_index + 1:03d}",
        "consent_confirmed": True,
        "license_scope": ["training", "evaluation", "portfolio_demo"],
        "status": "active",
        "valid_from": "2026-01-01",
        "valid_until": "2027-12-31",
        "territory": "DEMO",
        "rights_holder_id": f"DEMO-RIGHTS-HOLDER-{author_index + 1:02d}",
        "demo": True,
    }


def _story_text(index: int) -> str:
    name = NAMES[index]
    city = CITIES[index // 2]
    profession = PROFESSIONS[index]
    evidence = OBJECTS[index]
    conflict = CONFLICTS[index]
    ally = ALLIES[index]
    reversal = REVERSALS[index]
    resolution = RESOLUTIONS[index]
    opening_styles = [
        f"{city}连下三天雨时，{name}在工作台最底层发现了{evidence}。",
        f"凌晨四点十七分，{name}结束一场漫长值班，{evidence}却让她重新推开办公室的灯。",
        f"{name}原以为这只是一次普通复核，直到{evidence}与系统中的记录完全对不上。",
        f"公开说明会开始前二十分钟，身为{profession}的{name}收到了{evidence}。",
        f"{city}的风掠过高架桥，{name}把{evidence}装进证物袋，决定不再沉默。",
    ]
    opening = opening_styles[index % len(opening_styles)]
    unique_code = f"“月桂-{index + 1:02d}”"
    return (
        f"{opening}\n"
        f"她在{city}做了七年{profession}，习惯让每个判断都留下可复核的依据。"
        f"这一次，{conflict}。所有人都劝她把异常写成偶发问题，甚至有人拿晋升和家人的安稳暗示她退让。"
        f"{name}没有立刻争辩，而是给调查建立代号{unique_code}，逐项封存原件、复制校验值，并把每一次接触证据的人写进时间线。\n"
        f"最难的不是找到线索，而是证明线索没有被她自己误读。她请来{ally}，两人把纸面记录、设备日志和现场口述分开核验。"
        f"第一次交叉比对失败后，她主动推翻自己的假设；第二次复核时，三个彼此独立的时间点终于闭合。"
        f"就在她准备提交报告时，对方抢先发布声明，把她描述成因私人恩怨报复组织的人。她短暂犹豫，却没有删除任何原始文件。\n"
        f"转折发生在公开质询当天：{reversal}。{name}没有用情绪反击，而是依次展示来源、处理步骤和可以由第三方重复的验证方法。"
        f"曾经沉默的人开始补充证词，原本被推到台前承担责任的年轻女性也终于获得说明机会。"
        f"对方试图用一笔优厚和解金结束争议，她拒绝了附带保密条款的条件。\n"
        f"最终，她选择{resolution}。事情没有以童话式胜利收尾：她失去一个重要合作机会，也花了数月修复信任。"
        f"但新的制度开始运转，后来者不必再靠孤勇保存真相。夜色降临时，{name}把调查代号从白板上擦掉，只留下最后一句备注："
        f"证据不是武器，它首先是一条让普通人能够返回事实的路。"
    )


def generate_base_stories() -> list[dict[str, Any]]:
    """Return exactly 20 unique, rights-cleared synthetic source stories."""
    stories: list[dict[str, Any]] = []
    for index in range(20):
        author_index = index // 2
        story_number = index + 1
        stories.append(
            {
                "record_id": f"RAW-{story_number:03d}",
                "source_id": f"DEMO-SOURCE-{story_number:03d}",
                "document_id": f"DEMO-DOCUMENT-{story_number:03d}",
                "rights_record_id": f"DEMO-RIGHTS-{story_number:03d}",
                "ingest_sequence": story_number,
                "source_uri": f"demo://commissioned/author-{author_index + 1:02d}/work-{story_number:03d}",
                "source_type": "synthetic_commissioned_demo",
                "author_id": f"DEMO-AUTHOR-{author_index + 1:02d}",
                "work_id": f"DEMO-WORK-{story_number:03d}",
                "title": f"{NAMES[index]}：{OBJECTS[index]}",
                "genre": "大女主现实向短篇",
                "language": "zh-CN",
                "text": _story_text(index),
                "rights": _rights(author_index),
                "demo_marker": DEMO_MARKER,
                "demo": True,
            }
        )
    return stories


def _copy_as_defect(
    source: dict[str, Any],
    *,
    record_id: str,
    ingest_sequence: int,
    source_uri: str,
) -> dict[str, Any]:
    result = deepcopy(source)
    result["record_id"] = record_id
    result["source_id"] = f"DEMO-SOURCE-{record_id}"
    result["ingest_sequence"] = ingest_sequence
    result["source_uri"] = source_uri
    return result


def generate_raw_records() -> list[dict[str, Any]]:
    """Return 27 records with intentional rights, exact-dup, and near-dup defects."""
    base = generate_base_stories()
    records = list(base)

    records.append(
        _copy_as_defect(
            base[0],
            record_id="RAW-021",
            ingest_sequence=21,
            source_uri="demo://defect/exact-copy-001",
        )
    )
    records.append(
        _copy_as_defect(
            base[7],
            record_id="RAW-022",
            ingest_sequence=22,
            source_uri="demo://defect/exact-copy-002",
        )
    )

    for offset, source_index in enumerate((2, 11, 17), start=23):
        near = _copy_as_defect(
            base[source_index],
            record_id=f"RAW-{offset:03d}",
            ingest_sequence=offset,
            source_uri=f"demo://defect/near-copy-{offset - 22:03d}",
        )
        near["text"] = near["text"].replace("她短暂犹豫", "她沉默了片刻", 1)
        near["text"] += f"\n编辑尾注：这是用于近重复检测的轻微修订版本{offset - 22}。"
        records.append(near)

    unlicensed = _copy_as_defect(
        base[4],
        record_id="RAW-026",
        ingest_sequence=26,
        source_uri="demo://defect/unlicensed-copy",
    )
    unlicensed["rights"] = {
        "contract_id": "",
        "consent_confirmed": False,
        "license_scope": [],
        "status": "unlicensed",
        "valid_from": "2026-01-01",
        "valid_until": "2027-12-31",
        "territory": "DEMO",
        "rights_holder_id": "DEMO-RIGHTS-HOLDER-INVALID",
        "demo": True,
    }
    unlicensed["rights_record_id"] = "DEMO-RIGHTS-INVALID-UNLICENSED"
    records.append(unlicensed)

    expired = _copy_as_defect(
        base[5],
        record_id="RAW-027",
        ingest_sequence=27,
        source_uri="demo://defect/expired-license-copy",
    )
    expired["rights"]["status"] = "expired"
    expired["rights"]["valid_until"] = "2026-01-31"
    expired["rights_record_id"] = "DEMO-RIGHTS-INVALID-EXPIRED"
    records.append(expired)
    return records
