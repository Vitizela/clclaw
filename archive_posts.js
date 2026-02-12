const { chromium } = require('playwright');
const fs = require('fs-extra');
const path = require('path');
const crypto = require('crypto');

const CONFIG_PATH = path.join(__dirname, 'config.json');
const OUTPUT_DIR = path.join(__dirname, '论坛存档');

// 文件名安全化处理
function sanitizeFilename(name) {
    return name.replace(/[<>:"/\\|?*]/g, '_').substring(0, 100);
}

// 主归档函数
async function archivePosts(authorsToScrape) {
    if (!authorsToScrape || authorsToScrape.length === 0) {
        console.error("错误：必须提供至少一个作者名。");
        process.exit(1);
    }

    console.log(`开始为作者 [${authorsToScrape.join(', ')}] 归档帖子...`);

    const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
    const { forumSectionUrl } = config;

    const browser = await chromium.launch();
    const context = await browser.newContext();
    const page = await context.newPage();

    let postUrls = [];

    try {
        // 1. 搜集所有相关作者的帖子链接
        console.log("阶段一：正在搜集帖子链接...");
        await page.goto(forumSectionUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });

        let currentPage = 1;
        while (true) {
            process.stdout.write(`...正在扫描第 ${currentPage} 页\r`);
            await page.waitForSelector('#tbody', { timeout: 60000 });

            const pagePostInfos = await page.$$eval('#tbody tr', (rows, authors) => {
                return rows.map(row => {
                    const authorElement = row.querySelector('.bl');
                    const titleElement = row.querySelector('h3 > a');
                    if (authorElement && titleElement && authors.includes(authorElement.textContent.trim())) {
                        return {
                            author: authorElement.textContent.trim(),
                            url: titleElement.href
                        };
                    }
                    return null;
                }).filter(Boolean);
            }, authorsToScrape);

            postUrls.push(...pagePostInfos);

            const nextPageButton = await page.$('a:has-text("下一頁")');
            if (nextPageButton && !(await nextPageButton.evaluate(node => node.classList.contains('gray')))) {
                await nextPageButton.click();
                await page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 60000 });
                currentPage++;
            } else {
                break;
            }
        }
        console.log(`\n链接搜集完成，共找到 ${postUrls.length} 个相关帖子。`);

        // 2. 逐一处理帖子
        console.log("\n阶段二：开始处理和归档帖子...");
        let newPostsCount = 0;
        for (let i = 0; i < postUrls.length; i++) {
            const { author, url } = postUrls[i];
            const progress = `(${(i + 1)}/${postUrls.length})`;
            
            try {
                await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
                
                const title = await page.$eval('h4.f16', el => el.textContent.trim());
                const timestamp = await page.$eval('span[data-timestamp]', el => el.getAttribute('data-timestamp'));
                const date = new Date(parseInt(timestamp, 10) * 1000);
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                
                const safeTitle = sanitizeFilename(title);
                const postDir = path.join(OUTPUT_DIR, sanitizeFilename(author), String(year), month, safeTitle);
                
                // 增量检查
                if (await fs.pathExists(postDir)) {
                    process.stdout.write(`-> ${progress} [跳过] ${author} - ${title}\n`);
                    continue;
                }
                
                process.stdout.write(`-> ${progress} [新增] ${author} - ${title}\n`);
                newPostsCount++;

                await fs.ensureDir(path.join(postDir, 'photo'));
                await fs.ensureDir(path.join(postDir, 'video'));
                
                // 提取和清理内容
                let contentHtml = await page.$eval('div.tpc_content#conttpc', el => el.innerHTML);
                // (此处可添加更复杂的HTML清理逻辑)
                let contentMarkdown = contentHtml
                    .replace(/<br\s*\/?>/gi, '\n')
                    .replace(/<a href="([^"]+)">([^<]+)<\/a>/gi, '[$2]($1)')
                    .replace(/<[^>]+>/g, '') // 移除所有其他HTML标签
                    .trim();

                const mdContent = `## ${title}\n\n**作者**: ${author}\n**发布日期**: ${date.toISOString()}\n\n---\n\n${contentMarkdown}`;
                await fs.writeFile(path.join(postDir, 'post.md'), mdContent);

                // 下载图片和视频 (示例逻辑)
                const mediaElements = await page.$$('div.tpc_content#conttpc img, div.tpc_content#conttpc video');
                for(const el of mediaElements) {
                    const src = await el.getAttribute('src');
                    if (src) {
                        try {
                            const response = await page.request.get(src);
                            const buffer = await response.body();
                            const filename = path.basename(new URL(src).pathname) || `${crypto.randomBytes(8).toString('hex')}.jpg`;
                            const type = (await el.evaluate(node => node.tagName)).toLowerCase();
                            const savePath = path.join(postDir, type === 'img' ? 'photo' : 'video', sanitizeFilename(filename));
                            await fs.writeFile(savePath, buffer);
                        } catch(e) {
                            console.warn(`   - 下载媒体失败 ${src}: ${e.message}`);
                        }
                    }
                }
            } catch (e) {
                console.error(`\n处理帖子 ${url} 时出错: ${e.message}`);
            }
        }
        console.log(`\n归档完成！新增了 ${newPostsCount} 篇帖子。`);

    } catch (error) {
        console.error(`\n发生严重错误: ${error.message}`);
    } finally {
        await browser.close();
    }
}

// 从命令行参数解析作者
const authors = process.argv.slice(2);
archivePosts(authors);
