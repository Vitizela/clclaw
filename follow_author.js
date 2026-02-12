const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const CONFIG_PATH = path.join(__dirname, 'config.json');

async function followAuthor(postUrl) {
    if (!postUrl) {
        console.error("错误：请提供一个帖子 URL。");
        process.exit(1);
    }

    // 1. 读取配置文件
    if (!fs.existsSync(CONFIG_PATH)) {
        console.error(`错误：配置文件 ${CONFIG_PATH} 不存在。`);
        process.exit(1);
    }
    const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));

    // 2. 提取作者
    console.log(`正在从 ${postUrl} 提取作者...`);
    const browser = await chromium.launch();
    const page = await browser.newPage();
    let authorName = '';

    try {
        await page.goto(postUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
        // 作者信息在第一个 .tr1 do_not_catch 元素内的 b 标签中
        const authorElement = await page.waitForSelector('.tr1.do_not_catch b', { timeout: 60000 });
        authorName = (await authorElement.textContent()).trim();
    } catch (error) {
        console.error(`提取作者失败: ${error.message}`);
        await browser.close();
        process.exit(1);
    } finally {
        await browser.close();
    }

    if (!authorName) {
        console.error("未能成功提取作者名。");
        return;
    }

    console.log(`成功提取作者: ${authorName}`);

    // 3. 更新关注列表
    if (config.followedAuthors.includes(authorName)) {
        console.log(`作者 ${authorName} 已经在您的关注列表中。`);
        return;
    }

    config.followedAuthors.push(authorName);
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
    console.log(`已将 ${authorName} 添加到您的关注列表。`);

    // 4. 触发首次全量归档
    console.log(`正在为 ${authorName} 触发首次全量归档，这可能需要一些时间...`);
    
    // 注意：这里我们直接调用 archive_posts.js。确保它在 PATH 中或提供正确路径。
    // 为了安全，我们对作者名进行转义，防止命令行注入。
    const escapedAuthorName = JSON.stringify(authorName);
    const archiveProcess = exec(`node archive_posts.js ${escapedAuthorName}`, (error, stdout, stderr) => {
        if (error) {
            console.error(`执行归档脚本时出错: ${error.message}`);
            return;
        }
        if (stderr) {
            console.error(`归档脚本报告错误: ${stderr}`);
            return;
        }
        console.log(`为 ${authorName} 的首次归档任务完成。
${stdout}`);
    });

    // 实时显示子进程的输出
    archiveProcess.stdout.on('data', (data) => {
        process.stdout.write(data);
    });
    archiveProcess.stderr.on('data', (data) => {
        process.stderr.write(data);
    });
}

const url = process.argv[2];
followAuthor(url);
