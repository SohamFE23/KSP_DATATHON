#!/usr/bin/env node
/**
 * SurakshaAI KSP Catalyst CLI
 */
const { program } = require('commander');
const riskCmd = require('../commands/risk');
const reportCmd = require('../commands/report');
const compareCmd = require('../commands/compare');

program
  .name('catalyst')
  .description('SurakshaAI KSP Crime Intelligence Platform CLI')
  .version('2.0.0');

program
  .command('risk <district>')
  .description('Fetch AI risk classification and composite 6D score for a district')
  .option('-y, --year <number>', 'Specify year')
  .action(riskCmd);

program
  .command('report <district>')
  .description('Generate executive crime report for a district')
  .action(reportCmd);

program
  .command('compare <districtA> <districtB>')
  .description('Compare risk profile of two districts side-by-side')
  .action(compareCmd);

program.parse(process.argv);
