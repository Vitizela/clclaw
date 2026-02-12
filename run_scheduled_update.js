const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const CONFIG_PATH = path.join(__dirname, 'config.json');

function runScheduledUpdate() {
    console.log("开始执行定时更新任务...");

    if (!fs.existsSync(CONFIG_PATH)) {
        console.error(`错误：配置文件 ${CONFIG_PATH} 不存在。`);
        process.exit(1);
    }
    const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
    const { followedAuthors } = config;

    if (!followedAuthors || followedAuthors.length === 0) {
        console.log("关注列表为空，无需更新。");
        return;
    }

    console.log(`准备为以下作者更新帖子: ${followedAuthors.join(', ')}`);

    // 为了安全，我们将每个作者名作为单独的、被引起来的参数传递
    const escapedAuthors = followedAuthors.map(author => JSON.stringify(author)).join(' ');

    const archiveProcess = exec(`node archive_posts.js ${escapedAuthors}`, (error, stdout, stderr) => {
        if (error) {
            console.error(`执行归档脚本时出错: ${error.message}`);
            return;
        }
        if (stderr) {
            console.error(`归档脚本报告错误: ${stderr}`);
            return;
        }
        console.log(`
定时更新任务完成。
${stdout}`);
    });

    archiveProcess.stdout.on('data', (data) => {
        process.stdout.write(data);
    });
    archiveProcess.stderr.on('data', (data) => {
        process.stderr.write(data);
    });
}

runScheduledUpdate();
