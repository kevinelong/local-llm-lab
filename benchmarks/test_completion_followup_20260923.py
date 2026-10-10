import unittest
import completion_followup_20260923 as experiment


class Protocol(unittest.TestCase):
    def test_schedule_and_gate(self):
        schedules = {s:experiment.entries_for(s) for s in ('smoke','ablation','staging')}
        self.assertEqual([len(schedules[s]) for s in schedules],[4,12,30])
        for rows in schedules.values():
            self.assertEqual(len(rows),len({r['label'] for r in rows}))
            self.assertTrue(all(r['loop_mode']=='observe' for r in rows))
        ablation=schedules['ablation']
        for a,b in zip(ablation[::2],ablation[1::2]):
            self.assertEqual((a['task'],a['repeat']),(b['task'],b['repeat']))
            self.assertEqual({a['prompt_mode'],b['prompt_mode']},{'baseline','completion'})
        def good(rows):
            return [dict(r,success=True,correct=True,clean_finish=True,completion_tokens_complete=True,
                         completion_tokens=100,inputs_unchanged=True) for r in rows]
        smoke, rows=good(schedules['smoke']),good(ablation)
        self.assertTrue(experiment.eligible(smoke,rows))
        smoke[0]['success']=False
        self.assertFalse(experiment.eligible(smoke,rows))
        smoke[0]['success']=True
        next(r for r in rows if r['prompt_mode']=='completion')['correct']=False
        self.assertFalse(experiment.eligible(smoke,rows))


if __name__=='__main__':
    unittest.main()
