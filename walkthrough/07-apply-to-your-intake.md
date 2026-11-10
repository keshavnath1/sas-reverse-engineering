# Apply the method to your own INTAKE

Start with one authorized SAS program and one business output. Write down
the question you want answered, such as “Does the summary depend on the
stateful preparation?” The same evidence-first approach applies even when
your project uses different SAS constructs.

1. **Scope the source.** Identify the entry point, allowed includes, expected
   source identities, and available input descriptors. Keep private material
   in the authorized inspection environment.
2. **Generate supported evidence.** Choose the appropriate existing review
   route. The public multi-file route requires a declared synthetic scope and
   profile. [Bounded source review](../scripts/review_source.py) is separate.
   Record unsupported or uninspected behavior and unresolved dependencies.
3. **Write the skills for the question.** Use the [skill format](04-how-to-write-the-skills.md).
   Give the LLM an evidence record to cite and a precise deliverable.
4. **Review the proposal.** Require one traceable requirement, one as-is
   dependency view, one justified design change, and one validation case.
   Record the business and runtime decisions that still need a person.

## Replay the teaching example

Use a Python 3.12 environment with the shared engine and its compatible
dependencies installed. From the root of the shared materials, run:

~~~sh
scratch=$(mktemp -d /tmp/sas-rea-example-XXXXXX)
scratch=$(cd "$scratch" && pwd -P)
mkdir "$scratch/INTAKE"
cp tests/fixtures/running-balance-workload/source/* "$scratch/INTAKE/"
evidence="/tmp/sas-re-int1-${scratch##*/}"
python3.12 -IB scripts/review_intake.py --intake "$scratch/INTAKE" --inventory
python3.12 -IB scripts/review_intake.py --p2a --modernization-drafts --intake "$scratch/INTAKE" --destination "$evidence"
evidence=$(cd "$evidence" && pwd -P)
python3.12 -IB scripts/run_running_balance.py --package "$evidence" --intake "$scratch/INTAKE"
~~~

Use fresh paths on each replay. The
[engine folder](../src/sas_re/README.md) explains the code with Mermaid.
The runnable example also uses the review script, public fixture, typed
profile, and candidate runner. The candidate only accepts the exact
supported public workload. Other projects can still receive a design
review where evidence supports it.

**Final team exercise:** Like an REA investigation, start from a concrete
question and ask what evidence would answer it. In this SAS workflow,
generate that evidence first, then give your skills clear questions and
checks. End with a modernization proposal the team can review and a list
of claims that still need proof.

[Back to the opening example](01-start-here.md)
