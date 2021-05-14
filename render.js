let response = fetch('munsell_real.json')
  .then(response => response.json())
  .then(colors => draw_illo(colors))

function draw_illo(colors) { 
  console.log('Plotting ' + colors.length + ' colors');
  let level_height = 15;
  let h_spacing = 15;
  let stroke = 8;

  let TAU = Zdog.TAU;
  let theta = TAU/40;

  var element = document.querySelector('#illo');

  let isSpinning = true;

  // create illo
  let illo = new Zdog.Illustration({
    element: element,
    rotate: {x : -TAU/12},
    zoom: 2,
    dragRotate: true,
    onDragStart: function() {
      isSpinning = false;
    }
  });

  for(var i = 0, len = colors.length; i < len; i++) {
    let color = colors[i]
    let angle = theta * color.hidx
    let r = h_spacing * color.C / 2
    let x = Math.cos(angle) * r;
    let z = Math.sin(angle) * r;
    new Zdog.Shape({
      addTo: illo,
      translate: { x: x, y: (5-color.V) * level_height, z: z },
      stroke: stroke,
      color: color.hex,
    })
  }

  // setup animation and render
  function animate() {
    if(isSpinning) {
      illo.rotate.y += 0.02
    }
    illo.updateRenderGraph()
    requestAnimationFrame(animate);
  }

  animate();
}