import urllib.request
import xml.etree.ElementTree as ET
import re
import trafilatura

# ==================== 请确认你的 GitHub 信息 ====================
GITHUB_USER = "zukuxi"            # 你的 GitHub 用户名
GITHUB_REPO = "x3-reddit-news"    # 你刚刚新建的仓库名字
# ==============================================================

url = "https://www.reddit.com/r/worldnews/top/.rss?t=day"
req = urllib.request.Request(
    url,
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 GitHubActions/1.0'}
)

try:
    print("正在连接 Reddit 获取最新热门新闻...")
    with urllib.request.urlopen(req) as response:
        atom_data = response.read()

    root = ET.fromstring(atom_data)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}

    # 创建符合 xteink 视界标准的 RSS 骨架
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Reddit World News (x3 Direct)"
    ET.SubElement(channel, "link").text = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}"
    ET.SubElement(channel, "description").text = "专为 xteink x3 优化，全文直接内嵌，点开即读"

    entries = root.findall('atom:entry', ns)
    print(f"成功获取列表！共 {len(entries)} 条新闻。开始抓取全文并直接注入...")

    for i, entry in enumerate(entries):
        title = entry.find('atom:title', ns).text
        content_html = entry.find('atom:content', ns).text or ""

        # 挖出真正的新闻外链
        match = re.search(r'<a href="([^"]+)">\[link\]</a>', content_html)
        real_link = match.group(1) if match else (entry.find('atom:link', ns).attrib['href'] if entry.find('atom:link', ns) is not None else "")

        if not real_link or ("reddit.com" in real_link and "/comments/" in real_link):
            link_elem = entry.find('atom:link', ns)
            real_link = link_elem.attrib['href'] if link_elem is not None else ""

        print(f"[{i+1}/{len(entries)}] 正在抓取正文: {title[:20]}...")

        # 利用 trafilatura 抽取新闻纯文本
        article_text = ""
        if real_link:
            try:
                downloaded = trafilatura.fetch_url(real_link)
                if downloaded:
                    article_text = trafilatura.extract(downloaded)
            except Exception as e:
                print(f"提取正文失败: {e}")

        if not article_text:
            article_text = "【正文抓取失败。可能由于外媒网站有反爬虫验证，或该新闻为纯视频/图片形式。】"

        # 排版：加上原文链接和分割线，让 xteink 屏幕显示更美观
        full_display_content = f"【原文链接】：{real_link}\n\n========================================\n\n{article_text}"

        # 写入单独的每一条新闻节点
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = real_link
        
        # ✨ 终极核心：把几千字的长篇正文直接作为描述写入 XML 内部！这样 x3 就不需要去下载 txt 了！
        ET.SubElement(item, "description").text = full_display_content

    # 输出唯一的 XML 文件
    tree = ET.ElementTree(rss)
    tree.write("worldnews.xml", encoding="utf-8", xml_declaration=True)
    print("✨ 大功告成！所有正文已成功注入一个 XML 文件中！")

except Exception as e:
    print(f"运行发生崩溃: {e}")
