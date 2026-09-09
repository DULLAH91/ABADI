(() => {
  const stations = [
    {
      number: '٠١',
      year: '١٧٢٧',
      type: 'البدايات',
      title: 'حين اجتمع<br><em>الحلم</em>',
      lead: 'في الدرعية، بدأت حكاية دولةٍ تنظر إلى أبعد من حدود المكان. خطوة أولى، تركت في الرمل أثرًا لا يمحوه الزمن.',
      note: 'كل رحلة عظيمة تبدأ من مكان صغير.',
      next: 'المحطة التالية'
    },
    {
      number: '٠٢',
      year: '١٩٣٢',
      type: 'التوحيد',
      title: 'رايةٌ واحدة<br><em>تجمعنا</em>',
      lead: 'من قلب الجزيرة، وحّد الملك عبدالعزيز أطراف البلاد تحت راية واحدة. صار للاسم وطن، وللوطن حكاية مشتركة.',
      note: 'الوحدة ليست نهاية الطريق، بل بدايته.',
      next: 'المحطة التالية'
    },
    {
      number: '٠٣',
      year: '٢٠٣٠',
      type: 'الامتداد',
      title: 'نحو أفق<br><em>أبعد</em>',
      lead: 'واليوم، تمضي المملكة بخطى واثقة نحو مستقبل يكتب فصله القادم. جذور راسخة، وأفق لا تحده السماء.',
      note: 'ما بدأ بالأمس، يصنع غدًا أكثر اتساعًا.',
      next: 'إعادة الرحلة'
    }
  ];

  const hero = document.querySelector('.hero-screen');
  const journey = document.querySelector('.journey-screen');
  const startButton = document.querySelector('[data-start]');
  const backButton = document.querySelector('[data-back]');
  const nextButton = document.querySelector('[data-next]');
  const tabs = [...document.querySelectorAll('.station-tab')];
  const aboutButton = document.querySelector('[data-about]');
  const brandLink = document.querySelector('.brand');
  const aboutPanel = document.querySelector('[data-about-panel]');
  const closeAbout = document.querySelector('[data-close-about]');
  const currentNumber = document.querySelector('#current-number');
  const stationIndex = document.querySelector('#station-index');
  const stationType = document.querySelector('#station-type');
  const journeyTitle = document.querySelector('#journey-title');
  const stationLead = document.querySelector('#station-lead');
  const stationNote = document.querySelector('#station-note-text');
  const visualYear = document.querySelector('#visual-year');
  const visualStation = document.querySelector('#visual-station');
  const nextLabel = document.querySelector('#next-label');
  let currentStation = 0;

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function showJourney() {
    hero.hidden = true;
    journey.hidden = false;
    updateStation(0, false);
    scrollToTop();
    setTimeout(() => nextButton.focus({ preventScroll: true }), 450);
  }

  function showHero() {
    journey.hidden = true;
    hero.hidden = false;
    scrollToTop();
    setTimeout(() => startButton.focus({ preventScroll: true }), 450);
  }

  function updateStation(index, animate = true) {
    currentStation = (index + stations.length) % stations.length;
    const station = stations[currentStation];

    const movingParts = [journeyTitle, stationLead, stationNote, document.querySelector('.journey-visual')];
    if (animate) movingParts.forEach((element) => element.classList.add('is-changing'));

    window.setTimeout(() => {
      currentNumber.textContent = station.number;
      stationIndex.textContent = station.number;
      stationType.textContent = station.type;
      journeyTitle.innerHTML = station.title;
      stationLead.textContent = station.lead;
      stationNote.textContent = station.note;
      visualYear.textContent = station.year;
      visualStation.textContent = station.number;
      nextLabel.textContent = station.next;
      journey.dataset.station = String(currentStation + 1);
      tabs.forEach((tab, tabIndex) => tab.classList.toggle('is-active', tabIndex === currentStation));
      movingParts.forEach((element) => element.classList.remove('is-changing'));
    }, animate ? 210 : 0);
  }

  function setAbout(open) {
    aboutPanel.classList.toggle('is-open', open);
    aboutPanel.setAttribute('aria-hidden', String(!open));
    document.body.classList.toggle('panel-open', open);
    if (open) setTimeout(() => closeAbout.focus(), 100);
    else setTimeout(() => aboutButton.focus(), 100);
  }

  startButton.addEventListener('click', showJourney);
  backButton.addEventListener('click', showHero);
  brandLink.addEventListener('click', (event) => {
    event.preventDefault();
    if (journey.hidden) scrollToTop();
    else showHero();
  });
  nextButton.addEventListener('click', () => updateStation(currentStation === stations.length - 1 ? 0 : currentStation + 1));
  tabs.forEach((tab) => tab.addEventListener('click', () => updateStation(Number(tab.dataset.station))));
  aboutButton.addEventListener('click', () => setAbout(true));
  closeAbout.addEventListener('click', () => setAbout(false));
  aboutPanel.addEventListener('click', (event) => { if (event.target === aboutPanel) setAbout(false); });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && aboutPanel.classList.contains('is-open')) setAbout(false);
    if (journey.hidden || aboutPanel.classList.contains('is-open')) return;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') updateStation(currentStation + 1);
    if (event.key === 'ArrowRight' || event.key === 'ArrowUp') updateStation(currentStation - 1);
  });

  // A small touch gesture keeps the story comfortable on phones.
  let touchStartX = 0;
  journey.addEventListener('touchstart', (event) => { touchStartX = event.changedTouches[0].screenX; }, { passive: true });
  journey.addEventListener('touchend', (event) => {
    const distance = event.changedTouches[0].screenX - touchStartX;
    if (Math.abs(distance) > 55) updateStation(currentStation + (distance < 0 ? 1 : -1));
  }, { passive: true });
})();
