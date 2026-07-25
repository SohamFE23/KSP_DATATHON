const { exec } = require('child_process');
const path = require('path');

module.exports = function(district) {
  console.log(`Generating executive report for '${district}'...`);
  const scriptPath = path.resolve(__dirname, '../../pipeline/08_report_generator.py');
  const cmd = `python "${scriptPath}" --district "${district}"`;

  exec(cmd, (error, stdout, stderr) => {
    if (error) {
      console.error(`❌ Error generating report: ${error.message}`);
      return;
    }
    console.log(stdout);
    console.log(`✅ Executive report ready in reports/ folder.`);
  });
};
