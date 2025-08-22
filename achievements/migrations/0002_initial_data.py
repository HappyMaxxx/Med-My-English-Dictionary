from django.db import migrations

def initial_achievements(apps, schema_editor):
    Achievement = apps.get_model('achievements', 'Achievement') 
    if not Achievement.objects.filter(ach_type='1').exists():
        Achievement.objects.create(
            name="Word Newbie",
            description="Your journey into the world of words has begun",
            requirements="Add 10 words",
            level=1,
            ach_type='1',
            icon='1.jpg',
        )

        Achievement.objects.create(
            name="Word Enthusiast",
            description="You are a true language enthusiast!",
            requirements="Add 50 words",
            level=2,
            ach_type='1',
            icon='2.jpg',
        )

        Achievement.objects.create(
            name="Lexicon Master",
            description="Your vocabulary is impressive",
            requirements="Add 100 words",
            level=3,
            ach_type='1',
            icon='3.jpg',
        )

        Achievement.objects.create(
            name="Group Creator",
            description="The first step to organizing knowledge",
            requirements="Create your first group",
            level=1,
            ach_type='2',
            icon='4.jpg',
        )

        Achievement.objects.create(
            name="Thematic Expert",
            description="Your groups cover a wide range of topics",
            requirements="Create 5 groups",
            level=2,
            ach_type='2',
            icon='5.jpg',
        )

        Achievement.objects.create(
            name="Group Curator",
            description="You are a true curator of words",
            requirements="Create 10 groups with at least 5 words in each group",
            level=3,
            ach_type='2',
            icon='6.jpg',
        )

        Achievement.objects.create(
            name="Social Starter",
            description="You start building your network of friends",
            requirements="Find 5 friends",
            level=1,
            ach_type='3',
            icon='7.jpg',
        )

        Achievement.objects.create(
            name="Networker",
            description="Your network of friends is expanding!",
            requirements="Find 20 friends",
            level=2,
            ach_type='3',
            icon='8.jpg',
        )

        Achievement.objects.create(
            name="Socialite",
            description="You are a real star!",
            requirements="Find 50 friends",
            level=3,
            ach_type='3',
            icon='9.jpg',
        )

        Achievement.objects.create(
            name="Avid Reader",
            description="You are actively expanding your knowledge",
            requirements="Read 5 texts and keep at least 1 word",
            level=1,
            ach_type='4',
            icon='10.jpg',
        )

        Achievement.objects.create(
            name="Bookworm",
            description="You are a true book lover!",
            requirements="Read 50 texts and keep at least 10 word",
            level=2,
            ach_type='4',
            icon='11.jpg',
        )

        Achievement.objects.create(
            name="Literary Scholar",
            description="A person who exists without a book seems strange and unnatural (Taras Shevchenko)",
            requirements="Read 100 texts and keep at least 20 word",
            level=3,
            ach_type='4',
            icon='12.jpg',
        )

        Achievement.objects.create(
            name="Friendly Learner",
            description="Why create a bicycle?",
            requirements="Start using 5 community groups",
            level=1,
            ach_type='5',
            icon='13.jpg',
        )

        Achievement.objects.create(
            name="Social Butterfly",
            description="Your words help others!",
            requirements="Share 10 of your groups",
            level=2,
            ach_type='5',
            icon='14.jpg',
        )

        Achievement.objects.create(
            name="Community Builder",
            description="You build a community around your dictionary",
            requirements="Develop your vocabulary and get 20 subscriptions to it",
            level=3,
            ach_type='5',
            icon='15.jpg',
        )

        Achievement.objects.create(
            name="Wordsmith",
            description="Your examples help us to understand the point better!",
            requirements="Add 10 words with examples",
            level=1,
            ach_type='6',
            icon='16.jpg',
        )

        Achievement.objects.create(
            name="Language Artisan",
            description="Your skill is amazing!",
            requirements="Add 50 words with examples",
            level=2,
            ach_type='6',
            icon='17.jpg',
        )

        Achievement.objects.create(
            name="Nietzsche",
            description="Your words have depth!",
            requirements="Add 100 words with examples",
            level=3,
            ach_type='6',
            icon='18.jpg',
        )

        Achievement.objects.create(
            name="Early Bird",
            description="You are a pioneer!",
            requirements="",
            level=1,
            ach_type='7',
            icon='19.jpg',
        )

        Achievement.objects.create(
            name="Marathoner",
            description="Everything that can be imagined is real (Pablo Picasso)",
            requirements="",
            level=1,
            ach_type='7',
            icon='20.jpg',
        )

        Achievement.objects.create(
            name="Perfectionist",
            description="Your attention to detail makes the dictionary perfect!",
            requirements="",
            level=1,
            ach_type='7',
            icon='21.jpg',
        )

        Achievement.objects.create(
            name="Gotta Catch 'Em All!",
            description="All Pokémon, oh, I mean, achievements are collected!",
            requirements="",
            level=1,
            ach_type='7',
            icon='22.jpg',
        )
        

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('achievements', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(initial_achievements),
    ]
