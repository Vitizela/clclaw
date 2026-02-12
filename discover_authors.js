const { chromium } = require('playwright');

async function discoverAuthors(forumSectionUrl) {
    if (!forumSectionUrl) {
        console.error("错误：必须提供论坛版块的 URL。");
        process.exit(1);
    }

    const browser = await chromium.launch();
    const page = await browser.newPage();
    const authors = new Set();

    try {
        await page.goto(forumSectionUrl, { waitUntil: 'domcontentloaded' });

        let nextPageExists = true;
        while (nextPageExists) {
            // 等待帖子列表加载完成
            await page.waitForSelector('tr.tr1 > th > b');

            // 提取当前页面的所有作者
            const authorNodes = await page.$$('tr.tr1 > th > b');
            for (const node of authorNodes) {
                const authorName = await node.textContent();
                authors.add(authorName.trim());
            }

            // 查找“下一頁”按钮
            const nextPageButton = await page.$('a:has-text("下一頁")');
            if (nextPageButton) {
                const isDisabled = await nextPageButton.evaluate(node => node.classList.contains('gray'));
                if (!isDisabled) {
                    await nextPageButton.click();
                    await page.waitForNavigation({ waitUntil: 'domcontentloaded' });
                } else {
                    nextPageExists = false; // 按钮是灰色的，表示是最后一页
                }
            } else {
                nextPageExists = false; // 找不到按钮，表示是最后一页
            }
        }
    } catch (error) {
        console.error(`在处理页面时发生错误: ${error.message}`);
    } finally {
        await browser.close();
    }

    // 将Set转换为数组并以JSON格式输出
    console.log(JSON.stringify(Array.from(authors), null, 2));
}

// 从命令行参数获取URL
const url = process.argv[2];
discoverAuthors(url);
